# AI Code Analysis Agent

CLI-инструмент, который анализирует код проектов из Git-репозиториев, ищет логические ошибки и уязвимости (без фокуса на стиль), сохраняет большие объемы кода в памяти (ChromaDB) и выводит результаты анализа. Вызовы LLM реализованы через LangChain.

## Возможности

- Клонирование проекта по Git-ссылке и автоматическая очистка временной папки.
- Поддержка языков: Python, C++, Java, SQL.
- Фокус на логических ошибках, некорректных условиях, ошибках индексов, уязвимостях.
- Чанкинг кода и хранение чанков в ChromaDB для сохранения контекста.
- Гибкие промпты для LLM вынесены в отдельные файлы.
- Планирование анализа (LLM), динамический выбор действий и финальная рефлексия.
- Генерация Markdown-отчета с результатами и рефлексией.

## Структура проекта

- `agent.py` — оркестратор анализа, обход файлов и вызовы модели.
- `model_api.py` — интеграция с OpenAI через LangChain, язык/промпты, чанкинг и память.
- `gigachat_api.py` — интеграция с GigaChat (по токену), совместима с логикой анализа.
- `groq_api.py` — интеграция с Groq (OpenAI-compatible).
- `project_loader.py` — клонирование репозитория в папку `sandbox` и очистка.
- `prompts/` — промпты по языкам с few-shot примерами.
- `main.py` — точка входа CLI.
- `.env` — переменные окружения (API ключ).
- `reporter.py` — формирование и сохранение Markdown-отчета.
- `memory.py` — внешний модуль памяти для хранения чанков кода.
- `chroma_db/` — локальное хранилище ChromaDB (данные живут внутри проекта).
- `langchain_client.py` — создание LangChain Chat модели с OpenAI-compatible параметрами.
- `langchain_utils.py` — преобразование сообщений к формату LangChain.

## Установка

Требуется Python 3.10+.

Рекомендуемые зависимости:
- `langchain-openai`
- `langchain-core`
- `chromadb` (опционально, для внешней памяти)
- `python-dotenv` (для загрузки `.env`)
 - `torch` и `transformers` (для локальных моделей)

Установка:

```bash
pip install langchain-openai langchain-core chromadb python-dotenv
```
Для локальной модели:

```bash
pip install torch transformers
```

## Настройка ключей

В корне `ai_code_analyzer` создайте файл `.env` (уже добавлен):

```
OPENAI_API_KEY=your_key_here
GIGACHAT_API_TOKEN=your_gigachat_token_here
GROQ_API_KEY=your_groq_key_here
```

Либо экспортируйте переменную окружения вручную:

```bash
export OPENAI_API_KEY="your_key_here"
export GIGACHAT_API_TOKEN="your_gigachat_token_here"
export GROQ_API_KEY="your_groq_key_here"
```

При необходимости можно указать адрес API GigaChat:

```bash
export GIGACHAT_BASE_URL="https://gigachat.devices.sberbank.ru/api/v1"
export GROQ_BASE_URL="https://api.groq.com/openai/v1"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

## Запуск

```bash
python main.py [git_repo_url_or_path] 
```

Пример:

```bash
python main.py https://github.com/wjakob/nanobind_example
```

Пример для локального проекта (например, уже помещенного в `sandbox/`):

```bash
python main.py ./sandbox/project_name
```

Если запустить без аргументов, будет использован путь `./sandbox`:

```bash
python main.py
```

Для выбора провайдера:

```bash
python main.py https://github.com/user/project.git --provider gigachat --model GigaChat
```

Для Groq:

```bash
python main.py https://github.com/user/project.git --provider groq --model llama-3.1-8b-instant
```

Для локальной модели:

```bash
python main.py ./sandbox/project_name --provider local --model /home/vladislav/models/Phi-3.5-mini-instruct
```

Примечание: для GigaChat и Groq требуется действительный API-ключ.

## Как это работает

1. `project_loader.py` либо клонирует репозиторий в папку `sandbox`, либо использует локальный путь.
2. `agent.py` собирает список поддерживаемых файлов и запрашивает у LLM план анализа (`get_plan`).
3. `agent.py` для каждого файла выполняет динамическую цепочку действий:
   - базовый анализ (`primary_analysis`);
   - при наличии триггеров проблем (ошибки/уязвимости) запускает `deep_dive` с уточняющим фокусом.
4. `model_api.py`, `gigachat_api.py` или `groq_api.py` для каждого файла (через LangChain):
   - определяет язык по расширению,
   - выбирает системный промпт из `prompts/`,
   - делит код на чанки и сохраняет их в памяти (`memory.py`, ChromaDB или fallback),
   - добавляет контекст из памяти в запрос.
5. После завершения анализа `agent.py` вызывает финальную рефлексию (`model_api.reflect`).
6. `reporter.py` формирует Markdown-отчет, сохраняет его и печатает в консоль.
7. Временная папка проекта удаляется в `finally` блоке.

## Логика работы (подробнее)

### Планирование (Reasoning)
В начале анализа агент формирует план на основе списка файлов. План строится LLM и выводится в консоль. Он служит ориентиром для процесса анализа.

### Динамические действия (Action)
Для каждого файла агент выполняет базовый анализ. Если в результате обнаружены признаки критичных проблем (ключевые слова: ошибки, уязвимости, гонки, инъекции), агент автоматически запускает повторный анализ с дополнительным фокусом.

### Память (Memory)
Код делится на чанки по 500 символов и сохраняется в ChromaDB в папке `chroma_db/` рядом с проектом. Если ChromaDB недоступен, используется локальный fallback. При анализе агент может добавлять в промпт краткие фрагменты из памяти.

### Рефлексия (Reflection)
После анализа всех файлов агент формирует итоговую самооценку: что найдено, где могли быть пробелы, какие шаги стоит добавить. Эта рефлексия попадает в отчет.

## Расширение языков

Добавьте новый файл промпта в `prompts/` и расширьте карту языков в `analysis_api_base.py`:

- `detect_language()` — сопоставление расширения с языком
- `_get_language_prompt()` — выбор промпта
- `_get_code_fence_lang()` — язык для code fence
