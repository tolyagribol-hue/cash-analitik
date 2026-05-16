from __future__ import annotations

import json
import math
import random
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


@dataclass
class Transaction:
    tx_date: date
    category: str
    amount: float
    kind: str = "expense"


class BudgetEngine:
    def __init__(self) -> None:
        self.categories = [
            "Дом",
            "Еда",
            "Транспорт",
            "Путешествия",
            "Здоровье",
            "Образование",
            "Развлечения",
            "Подписки",
        ]
        self.monthly_limits = {
            "Дом": 40000,
            "Еда": 25000,
            "Транспорт": 12000,
            "Путешествия": 10000,
            "Здоровье": 8000,
            "Образование": 7000,
            "Развлечения": 9000,
            "Подписки": 3000,
        }
        self.transactions: list[Transaction] = []

    def _seed_transactions(self) -> list[Transaction]:
        today = date.today()
        transactions: list[Transaction] = []
        baseline = {
            "Дом": 36000,
            "Еда": 24000,
            "Транспорт": 10000,
            "Путешествия": 9000,
            "Здоровье": 7000,
            "Образование": 6000,
            "Развлечения": 11000,
            "Подписки": 3200,
        }
        for month_offset in range(0, 5):
            month_anchor = today.replace(day=1) - timedelta(days=month_offset * 30)
            income_value = random.uniform(110000, 140000)
            transactions.append(
                Transaction(
                    tx_date=month_anchor.replace(day=5),
                    category="Пополнение",
                    amount=income_value,
                    kind="income",
                )
            )
            for category, base_value in baseline.items():
                fluctuation = random.uniform(0.85, 1.2)
                monthly_sum = base_value * fluctuation
                chunks = random.randint(3, 6)
                for _ in range(chunks):
                    day = random.randint(1, 27)
                    tx_date = month_anchor.replace(day=day)
                    transactions.append(
                        Transaction(
                            tx_date=tx_date,
                            category=category,
                            amount=monthly_sum / chunks,
                        )
                    )
        return transactions

    def monthly_totals(self, year: int, month: int) -> dict[str, float]:
        income_total = 0.0
        expense_total = 0.0
        for tx in self.transactions:
            if tx.tx_date.year == year and tx.tx_date.month == month:
                if tx.kind == "income":
                    income_total += tx.amount
                elif tx.kind == "expense":
                    expense_total += tx.amount
        return {
            "income": income_total,
            "expense": expense_total,
            "balance": income_total - expense_total,
        }

    def add_transaction(self, kind: str, amount: float, category: str) -> dict[str, float | str]:
        clean_kind = kind.lower().strip()
        if clean_kind not in {"income", "expense"}:
            raise ValueError("Неверный тип операции.")
        if amount <= 0:
            raise ValueError("Сумма должна быть больше нуля.")

        final_category = "Пополнение" if clean_kind == "income" else category
        if clean_kind == "expense" and final_category not in self.categories:
            raise ValueError("Неизвестная категория расхода.")

        tx = Transaction(
            tx_date=date.today(),
            category=final_category,
            amount=amount,
            kind=clean_kind,
        )
        self.transactions.append(tx)
        return {
            "kind": tx.kind,
            "category": tx.category,
            "amount": tx.amount,
        }

    def expenses_by_category(self, year: int, month: int) -> dict[str, float]:
        total_by_category = {cat: 0.0 for cat in self.categories}
        for tx in self.transactions:
            if tx.kind == "expense" and tx.tx_date.year == year and tx.tx_date.month == month:
                total_by_category[tx.category] += tx.amount
        return total_by_category

    def average_spend_last_months(self, category: str, months: int = 3) -> float:
        today = date.today()
        total = 0.0
        for offset in range(months):
            anchor = today.replace(day=1) - timedelta(days=offset * 30)
            month_data = self.expenses_by_category(anchor.year, anchor.month)
            total += month_data.get(category, 0.0)
        return total / months if months else 0.0

    def what_if_projection(self, category: str, cut_percent: int, months: int) -> dict[str, float]:
        avg_monthly = self.average_spend_last_months(category)
        monthly_saving = avg_monthly * (cut_percent / 100.0)
        return {
            "avg_monthly": avg_monthly,
            "monthly_saving": monthly_saving,
            "period_saving": monthly_saving * months,
            "new_monthly": avg_monthly - monthly_saving,
        }

    def anti_crisis_plan(self, year: int, month: int) -> list[dict[str, str | float]]:
        monthly_spend = self.expenses_by_category(year, month)
        today = date.today()
        days_passed = max(1, today.day)
        days_in_month = 30
        recommendations: list[dict[str, str | float]] = []
        for category, spent in monthly_spend.items():
            limit = self.monthly_limits.get(category, 0)
            projected = spent / days_passed * days_in_month
            if limit and (spent > limit or projected > limit):
                overrun = projected - limit
                cut_needed = min(45, max(10, math.ceil((overrun / projected) * 100)))
                recommendations.append(
                    {
                        "category": category,
                        "spent": spent,
                        "limit": limit,
                        "projected": projected,
                        "cut_percent": cut_needed,
                        "advice": (
                            f"Сократи расходы по категории «{category}» примерно на {cut_needed}% до конца месяца. "
                            f"Цель: уменьшить траты минимум на {max(0, overrun):,.0f}."
                        ),
                    }
                )
        recommendations.sort(key=lambda x: float(x["projected"]) - float(x["limit"]), reverse=True)
        return recommendations

    def _register_pdf_font(self) -> str:
        candidates = [
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/Library/Fonts/Arial.ttf"),
        ]
        for font_path in candidates:
            if font_path.exists():
                try:
                    pdfmetrics.registerFont(TTFont("AppFont", str(font_path)))
                    return "AppFont"
                except Exception:
                    continue
        return "Helvetica"

    def export_pdf(self, target: str) -> None:
        today = date.today()
        category_data = self.expenses_by_category(today.year, today.month)
        total = sum(category_data.values())
        top = sorted(category_data.items(), key=lambda x: x[1], reverse=True)[:3]
        anti_crisis = self.anti_crisis_plan(today.year, today.month)
        what_if = self.what_if_projection("Еда", 20, 6)

        if not target.lower().endswith(".pdf"):
            target += ".pdf"

        font_name = self._register_pdf_font()
        doc = canvas.Canvas(target, pagesize=A4)
        _, height = A4
        y = height - 50
        title_font = "Helvetica-Bold" if font_name == "Helvetica" else font_name
        doc.setFont(title_font, 16)
        doc.drawString(40, y, "Личный отчёт по бюджету")
        y -= 28
        doc.setFont(font_name, 11)
        doc.drawString(40, y, f"Итог месяца: общий расход {total:,.0f}")
        y -= 24
        doc.setFont(title_font, 12)
        doc.drawString(40, y, "Топ категорий")
        y -= 18
        doc.setFont(font_name, 11)
        for category, amount in top:
            doc.drawString(50, y, f"- {category}: {amount:,.0f}")
            y -= 16

        y -= 8
        doc.setFont(title_font, 12)
        doc.drawString(40, y, "Инсайт сценария")
        y -= 18
        doc.setFont(font_name, 11)
        doc.drawString(
            50,
            y,
            (
                "- Если сократить расходы на еду на 20%, прогноз экономии за 6 месяцев: "
                f"{what_if['period_saving']:,.0f}"
            ),
        )
        y -= 24
        doc.setFont(title_font, 12)
        doc.drawString(40, y, "Антикризисные рекомендации")
        y -= 18
        doc.setFont(font_name, 11)
        if anti_crisis:
            for row in anti_crisis[:5]:
                if y < 80:
                    doc.showPage()
                    y = height - 50
                    doc.setFont(font_name, 11)
                doc.drawString(
                    50,
                    y,
                    f"- {row['category']}: сократить на {row['cut_percent']}% (прогноз {float(row['projected']):,.0f})",
                )
                y -= 16
        else:
            doc.drawString(50, y, "- Критичных сокращений не требуется.")

        doc.save()


class WebBridge(QObject):
    def __init__(self, engine: BudgetEngine, window: "MainWindow") -> None:
        super().__init__()
        self.engine = engine
        self.window = window

    @Slot(result="QString")
    def getInitialData(self) -> str:
        today = date.today()
        category_map = self.engine.expenses_by_category(today.year, today.month)
        totals = self.engine.monthly_totals(today.year, today.month)
        total = sum(category_map.values())
        categories = [
            {"name": name, "amount": amount}
            for name, amount in sorted(category_map.items(), key=lambda item: item[1], reverse=True)
        ]
        payload = {
            "categories": categories,
            "total": total,
            "income": totals["income"],
            "balance": totals["balance"],
            "month": f"{today.month:02d}.{today.year}",
            "limits": self.engine.monthly_limits,
        }
        return json.dumps(payload, ensure_ascii=False)

    @Slot(result="QString")
    def getCategories(self) -> str:
        return json.dumps(self.engine.categories, ensure_ascii=False)

    @Slot(str, int, int, result="QString")
    def calculateWhatIf(self, category: str, cut_percent: int, months: int) -> str:
        data = self.engine.what_if_projection(category, cut_percent, months)
        return json.dumps(data, ensure_ascii=False)

    @Slot(result="QString")
    def getAntiCrisisPlan(self) -> str:
        today = date.today()
        plan = self.engine.anti_crisis_plan(today.year, today.month)
        return json.dumps(plan, ensure_ascii=False)

    @Slot(result="QString")
    def exportPdf(self) -> str:
        target, _ = QFileDialog.getSaveFileName(
            self.window,
            "Сохранить отчёт",
            str(Path.home() / "otchet-byudzhet-insayty.pdf"),
            "PDF (*.pdf)",
        )
        if not target:
            return json.dumps({"ok": False, "message": "Отмена пользователем"}, ensure_ascii=False)
        try:
            self.engine.export_pdf(target)
            return json.dumps({"ok": True, "path": target}, ensure_ascii=False)
        except Exception as exc:
            QMessageBox.critical(self.window, "Ошибка", str(exc))
            return json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False)

    @Slot(str, float, str, result="QString")
    def addTransaction(self, tx_type: str, amount: float, category: str) -> str:
        try:
            created = self.engine.add_transaction(tx_type, amount, category)
            return json.dumps({"ok": True, "transaction": created}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False)

    @Slot(result="QString")
    def resetAllData(self) -> str:
        self.engine.transactions.clear()
        return json.dumps({"ok": True}, ensure_ascii=False)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Money Pro - Web GUI")
        self.resize(1280, 800)
        self.engine = BudgetEngine()

        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)

        self.channel = QWebChannel(self.web_view.page())
        self.bridge = WebBridge(self.engine, self)
        self.channel.registerObject("backend", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        web_index = base_dir / "web" / "index.html"
        self.web_view.setUrl(QUrl.fromLocalFile(str(web_index)))


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
