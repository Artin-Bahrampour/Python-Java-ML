FROM eclipse-temurin:21-jdk-jammy AS build
WORKDIR /src
COPY src /src/src
RUN mkdir -p /out && find src/main/java -name '*.java' -print0 | xargs -0 javac --release 21 -Xlint:all -d /out/classes

FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
RUN useradd --system --uid 10001 appuser
COPY --from=build /out/classes /app/classes
USER 10001
EXPOSE 8080
ENTRYPOINT ["java", "-cp", "/app/classes", "com.artin.reconciliation.Main", "serve", "--port", "8080"]
