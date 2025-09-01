from utilities import _normalize_selection



result1, result2 = _normalize_selection(selection=None)

print("Result", result1, result2)

selection = {
  "right box": ["green", "blue", "yellow"],
  "left box":  ["white", "blue", "red"],
 }

result3, result4 = _normalize_selection(selection=selection)

print("Result", result3, result4)