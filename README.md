# Инструкция по запуску

1.  Запустить Google Chrome в режиме удаленной отладки:

```
google-chrome --remote-debugging-port=9222 --user-data-dir="~/ChromeProfile"
```

2.  Перейти на сайт https://geotastic.net/home и залогиниться.
3.  Нажать на "CREATE LOCAL GAME", а затем на "WATCH AD".
4.  На странице выбора режима игры установить необходимое количество раундов и их длительность (можно ∞).
5.  Начать игру и запустить бота:

```
python3 geotastic_bot.py -r ROUNDS_NUM [--fetch-location] [--remove-arrows]
```

ROUNDS_NUM - количество раундов.

fetch-location - извлекать страну и город из информации о погоде (иногда не прогружается).

remove-arrows - удалить из панорамы стрелки для передвижения.

**Во время игры браузер должен быть развернут на полный экран**
