FROM ghcr.io/cirruslabs/flutter:stable AS build

WORKDIR /app

ARG API_BASE_URL=http://localhost:8000

COPY . .

RUN rm -rf .dart_tool build
RUN flutter config --enable-web
RUN flutter pub get
RUN flutter build web --release --dart-define=API_BASE_URL=${API_BASE_URL}

FROM nginx:alpine

COPY --from=build /app/build/web /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]