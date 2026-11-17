package com.diet.security;

import com.diet.common.DomainException;

// 对齐 Flask utils/auth.py：身份校验规则全部集中在这一处
public class AuthSupport {

    public static void ensureSelf(Long rawUserId) {
        if (rawUserId == null) {
            return;
        }
        AuthContext.Identity me = AuthContext.get();
        if (me.isAdmin() || rawUserId.equals(me.userId())) {
            return;
        }
        throw new DomainException(403, "无权访问其他用户的数据");
    }

    // 普通用户默认操作自己；管理员必须显式指定 user_id
    public static Long resolveUserId(Long rawUserId) {
        if (rawUserId != null) {
            ensureSelf(rawUserId);
            return rawUserId;
        }
        AuthContext.Identity me = AuthContext.get();
        if (me.isAdmin()) {
            throw new DomainException(400, "管理员操作需指定 user_id");
        }
        return me.userId();
    }

    // 系统资源(owner 为空)所有人可见；个人资源仅本人/管理员
    public static boolean canView(Long ownerId) {
        if (ownerId == null) {
            return true;
        }
        AuthContext.Identity me = AuthContext.get();
        return me.isAdmin() || ownerId.equals(me.userId());
    }

    // 系统资源仅管理员可改；个人资源仅本人/管理员
    public static boolean canEdit(Long ownerId) {
        if (ownerId == null) {
            return AuthContext.get().isAdmin();
        }
        AuthContext.Identity me = AuthContext.get();
        return me.isAdmin() || ownerId.equals(me.userId());
    }

    public static void ensureEdit(Long ownerId) {
        if (canEdit(ownerId)) {
            return;
        }
        if (ownerId == null) {
            throw new DomainException(403, "系统数据仅管理员可修改");
        }
        throw new DomainException(403, "无权访问该资源");
    }
}
