"""
Executive PDF Report Generator for The Quest Hotel Management System.
Generates comprehensive financial, occupancy, and inventory reports using fpdf.
"""

import os
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

class QuestPDFReport(FPDF):
    def header(self):
        # Top Purple Accent Bar
        self.set_fill_color(59, 24, 95) # #3B185F
        self.rect(0, 0, 210, 8, "F")
        
        # Gold Accent Line
        self.set_fill_color(245, 158, 11) # #F59E0B
        self.rect(0, 8, 210, 2, "F")
        
        self.ln(6)
        self.set_font("Arial", "B", 18)
        self.set_text_color(59, 24, 95)
        self.cell(0, 8, "THE QUEST HOTEL", ln=True, align="C")
        
        self.set_font("Arial", "I", 9)
        self.set_text_color(120, 53, 15)
        self.cell(0, 5, '"We shall never deny a guest, even the most ridiculous request"', ln=True, align="C")
        
        self.set_font("Arial", "B", 12)
        self.set_text_color(30, 41, 59)
        self.cell(0, 7, "EXECUTIVE MANAGEMENT & FINANCIAL AUDIT REPORT", ln=True, align="C")
        
        self.set_draw_color(226, 232, 240)
        self.line(10, 32, 200, 32)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"The Quest Hotel Management System | Confidential | Page {self.page_no()}", align="C")

def generate_hotel_pdf_report(output_filepath: str, metrics: dict, transactions: list, room_stats: dict, admin_name: str = "Administrator") -> str:
    """
    Generates a professional PDF report containing financial summaries, transactions, and room occupancy.
    """
    pdf = QuestPDFReport(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Meta Info
    now_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(100, 6, f"Generated On: {now_str}", ln=False)
    pdf.cell(90, 6, f"Audited By: {admin_name}", ln=True, align="R")
    pdf.ln(3)

    # 1. Executive Summary KPIs Box
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, pdf.get_y(), 190, 28, "DF")
    
    start_y = pdf.get_y() + 3
    pdf.set_xy(12, start_y)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(59, 24, 95)
    pdf.cell(45, 5, "Total Revenue:", ln=False)
    pdf.cell(50, 5, "Total Running Costs:", ln=False)
    pdf.cell(50, 5, "Net Hotel Profit:", ln=False)
    pdf.cell(40, 5, "Total Guests:", ln=True)

    pdf.set_xy(12, start_y + 6)
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(16, 185, 129) # Green
    pdf.cell(45, 7, f"PHP {metrics.get('revenue', 0):,.2f}", ln=False)

    pdf.set_text_color(239, 68, 68) # Red
    pdf.cell(50, 7, f"PHP {metrics.get('costs', 0):,.2f}", ln=False)

    net_profit = metrics.get('revenue', 0) - metrics.get('costs', 0)
    pdf.set_text_color(59, 24, 95)
    pdf.cell(50, 7, f"PHP {net_profit:,.2f}", ln=False)

    pdf.set_text_color(245, 158, 11) # Gold
    pdf.cell(40, 7, f"{metrics.get('guests', 0)} registered", ln=True)

    pdf.set_xy(12, start_y + 14)
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(45, 4, "Utility Costs: PHP {:,.2f}".format(metrics.get('cost_utility', 0)), ln=False)
    pdf.cell(50, 4, "Goods Costs: PHP {:,.2f}".format(metrics.get('cost_goods', 0)), ln=False)
    margin = (net_profit / metrics.get('revenue', 1) * 100) if metrics.get('revenue', 0) > 0 else 0
    pdf.cell(50, 4, f"Profit Margin: {margin:.1f}%", ln=False)
    pdf.cell(40, 4, f"Occupancy: {room_stats.get('occupancy_pct', 0):.1f}%", ln=True)

    pdf.set_y(start_y + 24)
    pdf.ln(4)

    # 2. Room & Occupancy Breakdown
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(59, 24, 95)
    pdf.cell(0, 7, "1. Room Occupancy & Operational Status", ln=True)
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(59, 24, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(47, 6, "Total Rooms", 1, 0, "C", fill=True)
    pdf.cell(47, 6, "Occupied Rooms", 1, 0, "C", fill=True)
    pdf.cell(47, 6, "Reserved Rooms", 1, 0, "C", fill=True)
    pdf.cell(49, 6, "Vacant / Needs Service", 1, 1, "C", fill=True)

    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(30, 41, 59)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(47, 6, str(room_stats.get("total", 27)), 1, 0, "C")
    pdf.cell(47, 6, f"{room_stats.get('occupied', 0)} ({room_stats.get('occupancy_pct', 0):.1f}%)", 1, 0, "C")
    pdf.cell(47, 6, str(room_stats.get("reserved", 0)), 1, 0, "C")
    vacant_str = f"{room_stats.get('vacant', 0)} Vacant / {room_stats.get('needs_service', 0)} Service"
    pdf.cell(49, 6, vacant_str, 1, 1, "C")
    pdf.ln(5)

    # 3. Recent Transactions Table
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(59, 24, 95)
    pdf.cell(0, 7, "2. Recent Financial Transactions & Ledger Audit", ln=True)

    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(59, 24, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(20, 6, "Tx ID", 1, 0, "C", fill=True)
    pdf.cell(32, 6, "Type", 1, 0, "C", fill=True)
    pdf.cell(78, 6, "Description", 1, 0, "L", fill=True)
    pdf.cell(30, 6, "Amount (PHP)", 1, 0, "R", fill=True)
    pdf.cell(30, 6, "Date Recorded", 1, 1, "C", fill=True)

    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(30, 41, 59)
    row_alt = False
    for tx in transactions[:25]:
        pdf.set_fill_color(248, 250, 252 if row_alt else 255)
        tx_type = tx.get("type", "")
        amt = tx.get("amount", 0.0)
        
        pdf.cell(20, 5.5, f"#{tx.get('id', '')}", 1, 0, "C", fill=True)
        pdf.cell(32, 5.5, tx_type, 1, 0, "C", fill=True)
        
        # Truncate description if too long
        desc = tx.get("description", "")
        if len(desc) > 42:
            desc = desc[:39] + "..."
        pdf.cell(78, 5.5, desc, 1, 0, "L", fill=True)
        
        amt_str = f"+{amt:,.2f}" if tx_type == "Revenue" else f"-{amt:,.2f}"
        pdf.cell(30, 5.5, amt_str, 1, 0, "R", fill=True)
        pdf.cell(30, 5.5, str(tx.get("date_recorded", ""))[:16], 1, 1, "C", fill=True)
        row_alt = not row_alt

    pdf.ln(5)

    # 4. Certification signature line
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, "I hereby certify that the above metrics reflect the live database records of The Quest Hotel.", ln=True)
    pdf.ln(10)
    pdf.cell(70, 4, "____________________________________", ln=False)
    pdf.cell(70, 4, "____________________________________", ln=True)
    pdf.cell(70, 4, f"Prepared By: {admin_name}", ln=False)
    pdf.cell(70, 4, "Internal Hotel Auditor", ln=True)

    pdf.output(output_filepath, "F")
    return output_filepath
