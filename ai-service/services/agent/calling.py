import logging
from config import AI_MODEL
logger = logging.getLogger(__name__)
"""阶段 7.2：单轮 Tool Calling。

一次用户请求中，正常路径只执行一轮工具；只有工具失败时才允许修复一次，因此最多两轮。
模型负责“调什么”，后端负责“能不能调、怎么执行、执行几次”。
"""
import json
import logging
import time
from dataclasses import dataclass, field



from services.agent.tools import (
    TOOL_REGISTRY, ToolRegistry, ToolResult, to_openai_tool,
)
from services.ai_service import _get_client


MAX_TOOL_CALLS_PER_ROUND = 4

DEFAULT_SYSTEM_PROMPT = """你是饮食管理系统的助手。你只能基于工具返回的数据回答，不能编造食谱、热量、营养成分或用户资料。
规则：
1. 涉及用户资料、食谱候选、营养计算时，先调用工具，不要凭记忆回答。
2. 一次可以调用多个互不依赖的工具；例如同时需要用户资料和食谱候选时，必须在同一轮同时调用，不要先查一个再查另一个。
3. 工具返回 ok=false 时，根据 error_code 修正参数或如实告诉用户，不要假装成功。
4. 回答使用中文，简洁说明依据；不要输出 JSON，除非用户明确要求。
5. 不要询问或传递 user_id；当前用户身份由系统注入。
6. 用户问“早餐/午餐/晚餐/加餐吃什么、有什么推荐、有哪些选择”时，必须调用 search_recipes，不要只查用户资料后直接回答。
7. 只要用户提到具体餐次（早餐/午餐/晚餐/加餐），即使没有出现“食谱”或“推荐”，也必须调用 search_recipes；这是硬性要求，不能省略。
示例：用户问“晚餐有什么推荐？”时，应同一轮调用 get_user_profile 和 search_recipes(meal_type="dinner")，不要只调用 get_user_profile。"""


@dataclass
class SingleTurnResult:
    answer: str
    status: str
    ok: bool = True
    attempts: int = 0
    tool_rounds: int = 0
    tool_calls: list = field(default_factory=list)
    trace: list = field(default_factory=list)
    model: str = ''
    error: str | None = None

    def to_dict(self):
        return {
            'answer': self.answer,
            'status': self.status,
            'ok': self.ok,
            'attempts': self.attempts,
            'tool_rounds': self.tool_rounds,
            'tool_calls': self.tool_calls,
            'trace': self.trace,
            'model': self.model,
            'error': self.error,
        }


def _get(obj, name, default=None):
    """同时兼容 OpenAI SDK 对象和测试里的 dict/SimpleNamespace。"""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _latency_ms(started):
    return round((time.perf_counter() - started) * 1000, 1)


def _create_completion(client, messages, tools, model, tool_choice=None):
    started = time.perf_counter()
    kwargs = {
        'model': model,
        'messages': messages,
        'temperature': 0.2,
        'max_tokens': 1200,
    }
    if tools is not None:
        kwargs['tools'] = tools
    if tool_choice is not None:
        kwargs['tool_choice'] = tool_choice
    response = client.chat.completions.create(**kwargs)
    return response, _latency_ms(started)


def _read_message(response):
    choices = _get(response, 'choices') or []
    if not choices:
        raise ValueError('模型响应缺少 choices')
    message = _get(choices[0], 'message')
    if message is None:
        raise ValueError('模型响应缺少 message')
    return message


def _assistant_payload(message):
    """把模型返回的 tool_calls 原样放回 messages，保留 id 和 arguments 字符串。"""
    tool_calls = []
    for tc in (_get(message, 'tool_calls') or []):
        function = _get(tc, 'function') or {}
        tool_calls.append({
            'id': _get(tc, 'id') or '',
            'type': _get(tc, 'type') or 'function',
            'function': {
                'name': _get(function, 'name') or '',
                'arguments': _get(function, 'arguments') or '{}',
            },
        })
    return {
        'role': 'assistant',
        'content': _get(message, 'content') or '',
        'tool_calls': tool_calls,
    }


def _parse_arguments(raw):
    if raw is None or raw == '':
        return True, {}
    if isinstance(raw, dict):
        return True, raw
    try:
        return True, json.loads(raw)
    except (TypeError, ValueError):
        return False, None


def _execute_tool_call(tc, index, registry, user):
    call_id = _get(tc, 'id') or f'call_{index}'
    function = _get(tc, 'function') or {}
    name = _get(function, 'name') or ''
    raw_args = _get(function, 'arguments')
    started = time.perf_counter()

    parsed_ok, parsed_args = _parse_arguments(raw_args)
    if not parsed_ok:
        result = ToolResult(
            ok=False,
            error_code='invalid_arguments',
            message='工具参数不是合法 JSON',
        )
    else:
        result = registry.execute(name, parsed_args, user)

    record = {
        'id': call_id,
        'name': name,
        'arguments': parsed_args if parsed_ok else raw_args,
        'ok': result.ok,
        'error_code': result.error_code,
        'latency_ms': _latency_ms(started),
    }
    return call_id, record, result


def _tool_payload(call_id, result):
    return {
        'role': 'tool',
        'tool_call_id': call_id,
        'content': json.dumps(result.to_dict(), ensure_ascii=False, default=str),
    }


def _fallback_answer(records):
    if not records:
        return '我暂时无法完成这次查询，请稍后重试。'
    if any(record['ok'] for record in records):
        return '我已经查到部分数据，但生成最终回答时出现问题，请稍后重试。'
    return '这次查询没有成功，请换一种问法或稍后重试。'


def _looks_like_tool_markup(text):
    """部分模型在最终回答阶段会把工具调用写成 DSML/XML 正文。"""
    return any(marker in (text or '') for marker in ('DSML', '<|tool_calls', '<｜tool_calls'))


def _final_retry_messages(question, observations):
    """换一份干净的上下文做最终回答，避免模型被上一轮 tool_calls 带偏。"""
    lines = []
    for observation in observations:
        payload = json.dumps(observation['result'], ensure_ascii=False, default=str)
        lines.append(f"- {observation['name']}: {payload}")
    evidence = '\n'.join(lines) if lines else '-（没有工具结果）'
    return [
        {
            'role': 'system',
            'content': DEFAULT_SYSTEM_PROMPT + (
                '\n这是最终回答阶段：只根据用户问题和工具结果回答，'
                '禁止输出工具调用、DSML、XML 标记。'
            ),
        },
        {
            'role': 'user',
            'content': f'用户问题：{question}\n\n工具结果：\n{evidence}\n\n请直接回答。',
        },
    ]


def run_single_turn(
    user,
    message,
    *,
    client=None,
    registry: ToolRegistry | None = None,
    system_prompt=None,
    max_tool_retries=1,
):
    """执行一次单轮 Tool Calling。

    - 正常路径：模型 → 工具 → observation → 模型最终回答
    - 工具失败：允许模型看到错误后修正一次；最多两轮工具执行
    - 最终回答阶段禁止再调用工具；若模型把调用意图写进正文，换干净上下文重答一次
    """
    message = (message or '').strip()
    started = time.perf_counter()
    trace = []
    records = []
    observations = []
    model = AI_MODEL

    if not message:
        return SingleTurnResult(
            answer='请输入你的问题。',
            status='invalid_request',
            ok=False,
            model=model,
            error='empty_message',
        )
    if len(message) > 2000:
        return SingleTurnResult(
            answer='问题太长，请控制在 2000 字以内。',
            status='invalid_request',
            ok=False,
            model=model,
            error='message_too_long',
        )

    registry = registry or TOOL_REGISTRY
    if client is None:
        client = _get_client()
    if client is None:
        return SingleTurnResult(
            answer='AI 服务尚未配置，请先在 .env 中设置 AI_API_KEY。',
            status='unavailable',
            ok=False,
            model=model,
            error='ai_not_configured',
        )

    tools = [to_openai_tool(spec) for spec in registry.specs()]
    messages = [
        {'role': 'system', 'content': system_prompt or DEFAULT_SYSTEM_PROMPT},
        {'role': 'user', 'content': message},
    ]

    try:
        retries = max(0, min(int(max_tool_retries), 1))
    except (TypeError, ValueError):
        retries = 1
    max_rounds = 1 + retries

    attempts = 0
    tool_rounds = 0
    had_failure = False
    last_failures = 0
    model_failed = False

    for round_index in range(max_rounds):
        attempts += 1
        try:
            response, latency = _create_completion(client, messages, tools, model)
            msg = _read_message(response)
            content = (_get(msg, 'content') or '').strip()
            tool_calls = list(_get(msg, 'tool_calls') or [])
        except Exception as exc:
            model_failed = True
            trace.append({
                'event': 'model_call',
                'round': attempts,
                'ok': False,
                'error': type(exc).__name__,
                'latency_ms': _latency_ms(started),
            })
            logger.exception('单轮 Tool Calling 模型调用失败')
            break

        trace.append({
            'event': 'model_call',
            'round': attempts,
            'ok': True,
            'tool_calls': len(tool_calls),
            'latency_ms': latency,
        })

        if not tool_calls:
            status = 'repaired' if had_failure else ('answered' if tool_rounds == 0 else 'tool_answered')
            return SingleTurnResult(
                answer=content,
                status=status,
                ok=True,
                attempts=attempts,
                tool_rounds=tool_rounds,
                tool_calls=records,
                trace=trace,
                model=model,
            )

        messages.append(_assistant_payload(msg))
        round_failures = 0

        for index, tc in enumerate(tool_calls):
            if index >= MAX_TOOL_CALLS_PER_ROUND:
                call_id = _get(tc, 'id') or f'call_{index}'
                result = ToolResult(
                    ok=False,
                    error_code='tool_limit_exceeded',
                    message=f'单轮最多执行 {MAX_TOOL_CALLS_PER_ROUND} 个工具调用',
                )
                record = {
                    'id': call_id,
                    'name': _get(_get(tc, 'function') or {}, 'name') or '',
                    'arguments': None,
                    'ok': False,
                    'error_code': result.error_code,
                    'latency_ms': 0,
                }
            else:
                call_id, record, result = _execute_tool_call(tc, index, registry, user)

            records.append(record)
            observations.append({'name': record['name'], 'result': result.to_dict()})
            messages.append(_tool_payload(call_id, result))
            trace.append({
                'event': 'tool_call',
                'round': attempts,
                'name': record['name'],
                'ok': result.ok,
                'error_code': result.error_code,
                'latency_ms': record['latency_ms'],
            })
            if not result.ok:
                round_failures += 1

        tool_rounds += 1
        had_failure = had_failure or round_failures > 0
        last_failures = round_failures

        if round_failures == 0:
            break
        if round_index + 1 >= max_rounds:
            break

    # 工具已经执行过，或模型中途失败：再给模型一次“只回答、不再调工具”的机会
    if model_failed and not records:
        return SingleTurnResult(
            answer='AI 服务暂时不可用，请稍后重试。',
            status='model_error',
            ok=False,
            attempts=attempts,
            tool_rounds=tool_rounds,
            tool_calls=records,
            trace=trace,
            model=model,
            error='model_failed',
        )

    if model_failed and attempts > 1:
        return SingleTurnResult(
            answer=_fallback_answer(records),
            status='degraded',
            ok=True,
            attempts=attempts,
            tool_rounds=tool_rounds,
            tool_calls=records,
            trace=trace,
            model=model,
            error='model_failed',
        )

    attempts += 1
    try:
        # 保留 tools 但禁止选择，兼容部分模型：直接省略 tools 时它会把调用意图写进正文
        response, latency = _create_completion(
            client, messages, tools, model, tool_choice='none',
        )
        msg = _read_message(response)
        answer = (_get(msg, 'content') or '').strip()
        trace.append({
            'event': 'model_call',
            'round': attempts,
            'ok': True,
            'forced_answer': True,
            'latency_ms': latency,
        })

        if answer and not _looks_like_tool_markup(answer):
            status = 'degraded' if last_failures else ('repaired' if had_failure else 'tool_answered')
            return SingleTurnResult(
                answer=answer,
                status=status,
                ok=True,
                attempts=attempts,
                tool_rounds=tool_rounds,
                tool_calls=records,
                trace=trace,
                model=model,
                error='tool_failed' if last_failures else None,
            )

        # 模型把工具调用写进了正文：换一份不含 tool_calls 的干净上下文重答一次
        trace.append({
            'event': 'final_answer_invalid',
            'reason': 'tool_markup' if answer else 'empty',
        })
        attempts += 1
        try:
            retry_messages = _final_retry_messages(message, observations)
            retry_response, retry_latency = _create_completion(
                client, retry_messages, None, model,
            )
            retry_msg = _read_message(retry_response)
            retry_answer = (_get(retry_msg, 'content') or '').strip()
            trace.append({
                'event': 'model_call',
                'round': attempts,
                'ok': True,
                'final_retry': True,
                'latency_ms': retry_latency,
            })
            if retry_answer and not _looks_like_tool_markup(retry_answer):
                return SingleTurnResult(
                    answer=retry_answer,
                    status='degraded' if last_failures else 'repaired',
                    ok=True,
                    attempts=attempts,
                    tool_rounds=tool_rounds,
                    tool_calls=records,
                    trace=trace,
                    model=model,
                    error='tool_failed' if last_failures else None,
                )
        except Exception as exc:
            trace.append({
                'event': 'model_call',
                'round': attempts,
                'ok': False,
                'final_retry': True,
                'error': type(exc).__name__,
            })
            logger.exception('单轮 Tool Calling 最终重答失败')

        return SingleTurnResult(
            answer=_fallback_answer(records),
            status='degraded',
            ok=True,
            attempts=attempts,
            tool_rounds=tool_rounds,
            tool_calls=records,
            trace=trace,
            model=model,
            error='invalid_final_answer',
        )
    except Exception as exc:
        trace.append({
            'event': 'model_call',
            'round': attempts,
            'ok': False,
            'forced_answer': True,
            'error': type(exc).__name__,
            'latency_ms': _latency_ms(started),
        })
        logger.exception('单轮 Tool Calling 最终回答失败')
        return SingleTurnResult(
            answer=_fallback_answer(records),
            status='degraded',
            ok=True,
            attempts=attempts,
            tool_rounds=tool_rounds,
            tool_calls=records,
            trace=trace,
            model=model,
            error='model_failed',
        )
