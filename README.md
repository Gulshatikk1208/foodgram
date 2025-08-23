# FOODGRAM - веб-приложение для публикации рецептов
## Возможности проекта:
- Регистрация и аутентификация пользователей
- Добавление, редактирование и удаление рецептов
- Подписка на других авторов
- Добавление рецептов в избранное
- Формирование списка покупок с возможностью скачивания

## Как запустить проект:
1. Клонировать репозиторий и перейти в директорию с файлом docker-compose.yml:
```
git clone https://github.com/Gulshatikk1208/foodgram.git
cd foodgram/infra
```

2. В текущей директории создать файл .env и заполнить его переменными для подключения к базе данных PostgreSQL:
```
    DB_ENGINE=django.db.backends.postgresql
    DB_NAME=foodgram_db
    DB_USER=foodgram_user
    DB_PASSWORD=secretpassword
    DB_HOST=db
    DB_PORT=5432
```

3. Запустить проект:
```
docker compose up -d --build
```
* Миграции и сбор статики выполняются автоматически внутри контейнера backend при старте — вручную их делать не нужно.

### После запуска проект будет доступен по адресу: http://localhost:8050

# FOODGRAM - веб-приложение для публикации рецептов
## Возможности проекта:
- Регистрация и аутентификация пользователей
- Добавление, редактирование и удаление рецептов
- Подписка на других авторов
- Добавление рецептов в избранное
- Формирование списка покупок с возможностью скачивания

## Как запустить проект:
1. Клонировать репозиторий и перейти в директорию с файлом docker-compose.yml:
```
git clone https://github.com/Gulshatikk1208/foodgram.git
cd foodgram/infra
```

2. В текущей директории создать файл .env и заполнить его переменными для подключения к базе данных PostgreSQL:
```
    DB_ENGINE=django.db.backends.postgresql
    DB_NAME=foodgram_db
    DB_USER=foodgram_user
    DB_PASSWORD=secretpassword
    DB_HOST=db
    DB_PORT=5432
```

3. Запустить проект:
```
docker compose up -d --build
```
* Миграции и сбор статики выполняются автоматически внутри контейнера backend при старте — вручную их делать не нужно.

### После запуска проект будет доступен по адресу: http://localhost:8050
## Деплой на сервер

Деплой выполняется автоматически через GitHub Actions при push в ветку main.

### Workflow:

- Собирает образы backend и frontend.
- Публикует их на Docker Hub.
- По SSH заходит на сервер в каталог /home/user/foodgram и выполняет:
```
docker compose pull
docker compose down
docker compose up -d
```

* Требования к серверу:
  - установлены Docker и docker compose
  - репозиторий клонирован в /home/user/foodgram
  - в корне создан файл .env с переменными окружения:
  ```
  DB_ENGINE
  DB_NAME
  DB_USER
  DB_PASSWORD
  DB_HOST
  DB_PORT и др.
  ```

В Secrets репозитория необходимо указать:

- DOCKER_USERNAME
- DOCKER_PASSWORD
- SSH_HOST
- SSH_USER
- SSH_KEY
- SSH_PASSPHRASE
- TELEGRAM_TO
- TELEGRAM_TOKEN

### После успешного деплоя проект будет доступен по адресу: https://foodgram-app.duckdns.org/recipes

Автор проекта: Гульшат Гайфуллина (https://github.com/Gulshatikk1208)
