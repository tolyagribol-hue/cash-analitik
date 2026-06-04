[cash-architecture.md](https://github.com/user-attachments/files/28576191/cash-architecture.md)
https://vk.com/away.php?to=https%3A%2F%2Fdrive.google.com%2Ffile%2Fd%2F1zGlVLN3wwZSzi1on8pDTLqW9dc3DIhyw%2Fview%3Fusp%3Ddrive_link&utf=1
# Архитектура приложения (Budget / Cash)

Десктопное приложение для учёта бюджета: веб-интерфейс внутри Qt-окна, связь через QWebChannel и Python-бэкенд с движком расчётов.

## Общая схема

```mermaid
flowchart TB
    subgraph UI["Пользовательский интерфейс"]
        WEB["Веб-интерфейс<br/>HTML / JS"]
    end

    subgraph QT["Qt / PySide6"]
        MW["QMainWindow<br/>MainWindow"]
        WEV["QWebEngineView"]
        WCH["QWebChannel"]
    end

    subgraph BACKEND["Python Бэкенд"]
        WB["WebBridge<br/>QObject"]
        BE["BudgetEngine"]

        subgraph METHODS["Методы BudgetEngine"]
            M1["_seed_transactions"]
            M2["monthly_totals"]
            M3["expenses_by_category"]
            M4["average_spend_last_months"]
            M5["what_if_projection"]
            M6["anti_crisis_plan"]
            M7["export_pdf"]
            M8["add_transaction"]
        end

        subgraph MODELS["Модели данных"]
            TX["Transaction<br/>tx_date, category, amount, kind"]
        end
    end

    subgraph EXT["Внешние ресурсы"]
        FONTS["Шрифты<br/>arial.ttf / DejaVuSans.ttf"]
        PDF["PDF-отчёт"]
    end

    WEB <-->|"отображение"| WEV
    MW --> WEV
    MW --> WB
    WEV --> WCH
    WCH --> WB
    WB --> BE

    BE --> M1
    BE --> M2
    BE --> M3
    BE --> M4
    BE --> M5
    BE --> M6
    BE --> M7
    BE --> M8
    BE --> TX

    M7 --> FONTS
    M7 --> PDF
```

## API WebBridge → веб-интерфейс

Методы, вызываемые из JavaScript через QWebChannel (пунктирные связи на исходной диаграмме):

```mermaid
flowchart LR
    WEB["Веб-интерфейс<br/>HTML / JS"]
    WB["WebBridge<br/>QObject"]

    WEB -.->|"getInitialData"| WB
    WEB -.->|"getCategories"| WB
    WEB -.->|"calculateWhatIf"| WB
    WEB -.->|"getAntiCrisisPlan"| WB
    WEB -.->|"exportPdf"| WB
    WEB -.->|"addTransaction"| WB
    WEB -.->|"resetAllData"| WB

    WB --> BE["BudgetEngine"]
```

## Слои

| Слой | Компоненты | Назначение |
|------|------------|------------|
| **Пользовательский интерфейс** | HTML / JS | UI: таблицы, графики, формы |
| **Qt / PySide6** | MainWindow, QWebEngineView, QWebChannel | Окно приложения и мост к веб-странице |
| **Python Бэкенд** | WebBridge, BudgetEngine | Бизнес-логика и расчёты |
| **Модели данных** | Transaction | Структура транзакции |
| **Внешние ресурсы** | Шрифты, PDF | Экспорт отчётов |

## Методы BudgetEngine

| Метод | Описание |
|-------|----------|
| `_seed_transactions` | Начальное заполнение тестовыми данными |
| `monthly_totals` | Итоги по месяцам |
| `expenses_by_category` | Расходы по категориям |
| `average_spend_last_months` | Средние траты за последние месяцы |
| `what_if_projection` | Прогноз «что если» |
| `anti_crisis_plan` | Антикризисный план |
| `export_pdf` | Экспорт отчёта в PDF |
| `add_transaction` | Добавление транзакции |

