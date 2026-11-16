"""Headless-Smoke-Test: Import, Summen, Export, PDFs."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
EXCEL = "/mnt/vibefs/uploads/5a58f482-1380-4825-9221-055594385eb5/7V16EFH4-261116_Kosten_Rev_5.xlsx"
import excel_io, pdf_out
from model import Project, VARIANT_KEYS
import calc
daten = excel_io.import_excel(EXCEL)
proj = Project()
proj.positionen = daten["positionen"]; proj.gruppen = daten["gruppen"]
proj.kostengruppen = daten["kostengruppen"]; proj.einheiten = daten["einheiten"]
print("Positionen:", len(proj.positionen), "| Gruppen:", len(proj.gruppen), "| KG:", len(proj.kostengruppen))
erwartet = {"basis": 7252800, "var1": 6170300, "var2": 6049900, "var3": 5979900}
totals = calc.total_summen(proj)
ok = True
for v in VARIANT_KEYS:
    treffer = v in erwartet and abs(totals[v] - erwartet[v]) < 0.5
    ok = ok and (treffer if v in erwartet else True)
    print(f"  {v}: {totals[v]:,.0f}".replace(",", "."), "OK" if treffer or v not in erwartet else "FEHLER")
excel_io.export_excel(proj, "/tmp/py-export.xlsx")
print("Excel-Export OK")
for art, fn in [("uebersicht", pdf_out.pdf_uebersicht), ("positionen", pdf_out.pdf_positionen), ("vergleich", pdf_out.pdf_vergleich)]:
    fn(proj, f"/tmp/py-test-{art}.pdf")
    print(f"PDF {art}: OK,", os.path.getsize(f'/tmp/py-test-{art}.pdf'), "Bytes")
print("BESTANDEN" if ok else "FEHLGESCHLAGEN")
