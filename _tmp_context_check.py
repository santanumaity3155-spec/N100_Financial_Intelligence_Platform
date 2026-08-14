import sys
sys.path.insert(0, ".")
from src.nlp.pros_cons_generator import get_company_context
import io

out = open("context_check.txt", "w")
# Check context for a few companies
for cid in ["TCS", "AXISBANK", "HDFCBANK", "INFY", "RELIANCE"]:
    ctx = get_company_context(cid)
    out.write("=== %s ===\n" % cid)
    out.write("is_financial: %s\n" % ctx.is_financial)
    out.write("sub_sector: %s\n" % ctx.sub_sector)
    out.write("latest_year: %s\n" % ctx.latest_year)
    out.write("history_years: %s\n" % ctx.history_years)
    out.write("latest metrics:\n")
    for k, v in sorted(ctx.latest.items()):
        out.write("  %s: %s\n" % (k, v))
    out.write("trailing metrics:\n")
    for k, v in sorted(ctx.trailing.items()):
        out.write("  %s: %s\n" % (k, v))
    out.write("\n")
out.close()
print("Done")
