# 🧱 1. Use OpenJDK 17 as the base image
FROM openjdk:17-jdk-slim

# 🧰 2. Install required tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tar \
    bash \
    procps \
 && rm -rf /var/lib/apt/lists/*

# 🧩 3. Install Maven (3.6.3)
ARG MAVEN_VERSION=3.6.3
ARG USER_HOME_DIR="/root"
ARG SHA=c35a1803a6e70a126e80b2b3ae33eed961f83ed74d18fcd16909b2d44d7dada3203f1ffe726c17ef8dcca2dcaa9fca676987befeadc9b9f759967a8cb77181c0
ARG BASE_URL=https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries

RUN mkdir -p /usr/share/maven /usr/share/maven/ref \
  && echo "📥 Downloading Maven..." \
  && curl -fsSL -o /tmp/apache-maven.tar.gz ${BASE_URL}/apache-maven-${MAVEN_VERSION}-bin.tar.gz \
  && echo "🔍 Verifying checksum..." \
  && echo "${SHA}  /tmp/apache-maven.tar.gz" | sha512sum -c - \
  && echo "📦 Extracting Maven..." \
  && tar -xzf /tmp/apache-maven.tar.gz -C /usr/share/maven --strip-components=1 \
  && ln -s /usr/share/maven/bin/mvn /usr/bin/mvn \
  && rm -f /tmp/apache-maven.tar.gz

ENV MAVEN_HOME /usr/share/maven
ENV MAVEN_CONFIG "$USER_HOME_DIR/.m2"

# 📂 4. Set the working directory
WORKDIR /app

# 📁 5. Copy project files
COPY . /app

# ⚙️ 6. Build the app
RUN mvn clean install -DskipTests

# 🌐 7. Expose the application port
EXPOSE 8080

# 🚀 8. Run the built JAR
CMD ["java", "-jar", "target/kakashi-jutsu-2.1.1.RELEASE.jar"]