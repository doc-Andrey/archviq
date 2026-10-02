# ARCHVIQ SITE V4 — изменения относительно V3

## Что сохранено из базового сайта
- общая визуальная стилистика и двухъязычный RU/EN интерфейс;
- верхняя навигация и основные кнопки;
- фото и блок автора проекта;
- существующие данные SILSO в репозитории;
- платные продуктовые ссылки;
- исходные когнитивные тесты, опросники и analysis_modules — для платного/private workflow.

## Что заменено
- публичный Engine 43-профиль заменён на текущий многослойный pipeline:
  `physical v0.1.1 -> SILSO context v2 -> RS4/v4 cascade v0.2 -> personal interpreter v0.1`;
- вместо старых 15 окон/X9 на бесплатной странице используются шесть окон W1–W3/F1–F3 и пакеты 5/7 дней;
- результат отображает параметры Processing Spiral, uncertainty, candidate brain circuits и pressure-only механизмы;
- соматика и психофизиология/психосоматика сохранены на бесплатной SSN-странице с обязательной меткой EXPERIMENTAL и без диагностических выводов.

## Данные
Никаких runtime-загрузок SILSO. В `data/` лежат:
- frozen `SN_d_tot_V2.0.txt`;
- reference banks 5/7 days;
- precomputed SILSO context v2;
- SHA256/manifest.

## Монетизация
- SSN-аналитика — бесплатно;
- cognitive tests — платно;
- questionnaires / GAP — платно;
- compatibility — платно;
- experimental somatic / psychophysiological branches входят в бесплатный SSN research output.
