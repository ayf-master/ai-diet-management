# 阶段1：Maven 编译打包
FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /build
COPY settings.xml /root/.m2/settings.xml
COPY pom.xml .
RUN mvn -q dependency:go-offline
COPY src ./src
RUN mvn -q package -DskipTests

# 阶段2：JRE 运行（alpine 体积小，1.9GB 内存的机器上更省）
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /build/target/*.jar app.jar
RUN mkdir -p /app/avatars
EXPOSE 9876
ENTRYPOINT ["java", \
  "-Xms128m", "-Xmx256m", "-XX:MaxMetaspaceSize=128m", \
  "-XX:+UseSerialGC", "-Djava.security.egd=file:/dev/./urandom", \
  "-jar", "app.jar"]
