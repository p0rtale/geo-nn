## Запуск бота

(не у всех работает :confused:)

```
python3 -m bot.geotastic_bot -r ROUNDS_NUM [--fetch-location] [--remove-arrows]
```

ROUNDS_NUM - количество раундов.

fetch-location - извлекать координаты.

remove-arrows - удалить из панорамы стрелки для передвижения.

**Во время игры браузер должен быть развернут на полный экран**

## Соединение изображений

```
python3 -m bot.crop_and_resize --input-dir INPUT --output-dir OUTPUT --n-from FROM --n-to TO --height HEIGHT [--clear]
```

INPUT - папка с фотографиями imageN_0, imageN_1, imageN_2, где N - номер раунда.

OUTPUT - путь к выходной директории.

FROM, TO - указывают номера раундов, для которых будут собраны фотографии.

HEIGHT - высота выходного изображения.

clear - удалять уже обработанные фотографии из INPUT.
