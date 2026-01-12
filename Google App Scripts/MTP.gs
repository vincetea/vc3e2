/***********************
 * WIDTH CALCULATION
 ***********************/
function calculateWidth(cellValue) {
  if (!cellValue) return ""; // leave empty if no text

  const charWidths = {
    " ": 6.125, "!": 4.375, "\"": 6.125, "#": 0, "$": 9.625, "%": 12.25, "&": 11.375,
    "'": 4.375, "(": 6.125, ")": 6.125, "*": 7, "+": 7, ",": 4.375, "-": 7, ".": 4.375,
    "/": 6.125, "0": 7.875, "1": 7.875, "2": 7.875, "3": 7.875, "4": 7.875, "5": 7.875,
    "6": 7.875, "7": 7.875, "8": 7.875, "9": 7.875, ":": 4.375, ";": 7, "<": 7, "=": 7,
    ">": 7, "?": 7, "@": 0, "A": 9.625, "B": 7.875, "C": 9.625, "D": 8.75, "E": 7.875,
    "F": 7.875, "G": 10.5, "H": 9.625, "I": 4.375, "J": 6.125, "K": 8.75, "L": 7.875,
    "M": 11.375, "N": 9.625, "O": 9.625, "P": 7.875, "Q": 10.5, "R": 8.75, "S": 7.875,
    "T": 8.75, "U": 9.625, "V": 9.625, "W": 12.25, "X": 9.625, "Y": 9.625, "Z": 8.75,
    "[": 6.125, "¥": 0, "]": 6.125, "^": 7, "_": 7, "`": 4.375,
    "a": 7, "b": 7, "c": 7, "d": 7, "e": 7, "f": 5.25, "g": 7, "h": 7, "i": 4.375,
    "j": 5.25, "k": 7, "l": 4.375, "m": 11.375, "n": 7, "o": 7.875, "p": 7, "q": 7,
    "r": 5.25, "s": 7, "t": 5.25, "u": 7, "v": 7.875, "w": 11.375, "x": 7, "y": 7,
    "z": 6.125, "{": 6.125, "|": 4.375, "}": 6.125, "~": 7, "…": 14
  };

  function isFullWidth(char) {
    const code = char.charCodeAt(0);
    return (
      (code >= 0x3000 && code <= 0x303F) ||
      (code >= 0x3040 && code <= 0x309F) ||
      (code >= 0x30A0 && code <= 0x30FF) ||
      (code >= 0x4E00 && code <= 0x9FFF) ||
      (code >= 0xFF00 && code <= 0xFFEF)
    );
  }

  const lines = cellValue.toString().split(/\r?\n/);
  return lines.map(line => {
    let total = 0;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (isFullWidth(ch)) total += 14;
      else if (charWidths[ch] !== undefined) total += charWidths[ch];
      else total += 1;
    }
    return total;
  }).join("\n");
}

/***********************
 * ON EDIT
 ***********************/
function onEdit(e) {
  const sheet = e.range.getSheet();
  const row = e.range.getRow();
  const col = e.range.getColumn();
  if (row <= 1) return; // skip header

  // Column A edited → update JP width (Column J) & checkbox (F)
  if (col === 1) {
    const valA = e.range.getValue();
    sheet.getRange(row, 10).setValue(valA ? calculateWidth(valA) : "");

    const checkboxCell = sheet.getRange(row, 6); // F
    if (valA !== "") {
      if (!checkboxCell.getDataValidation()) checkboxCell.insertCheckboxes();
    } else {
      checkboxCell.clearContent();
      checkboxCell.removeCheckboxes();
    }
  }

  // Column B edited → copy to C, update EN width (K) & Final width (L)
  if (col === 2) {
    const valB = e.range.getValue();
    sheet.getRange(row, 3).setValue(valB); // copy to C

    // EN width
    const enWidth = valB ? calculateWidth(valB) : "";
    sheet.getRange(row, 11).setValue(enWidth); // K

    // Final width (based on new value in C)
    const finalWidth = valB ? calculateWidth(valB) : "";
    sheet.getRange(row, 12).setValue(finalWidth); // L
  }

  // Column C edited directly → update Final width (L)
  if (col === 3) {
    const valC = e.range.getValue();
    sheet.getRange(row, 12).setValue(valC ? calculateWidth(valC) : "");
  }
}

/***********************
 * MENU
 ***********************/
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu("Width & Approved Tools")
    .addItem("✔️ Check All Approved", "checkAllReviewed")
    .addItem("❌ Uncheck All Approved", "uncheckAllReviewed")
    .addItem("✅ Add checkboxes for non-empty A rows", "addCheckboxesIfEdited")
    .addSeparator()
    .addItem("🖊 Update JP Widths (A → J)", "updateJPWidths")
    .addItem("🖊 Update EN Widths (B → K)", "updateENWidths")
    .addItem("🖊 Update Final Widths (C → L)", "updateFinalWidthsFromC")
    .addToUi();
}

/***********************
 * CHECKBOX HELPERS
 ***********************/
function checkAllReviewed() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getRange("A2:A" + sheet.getLastRow()).getValues();
  const checkboxes = data.map(r => [r[0] !== ""]);
  sheet.getRange("F2:F" + (checkboxes.length + 1)).setValues(checkboxes);
}

function uncheckAllReviewed() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  const checkboxes = Array(lastRow - 1).fill([false]);
  sheet.getRange("F2:F" + lastRow).setValues(checkboxes);
}

function addCheckboxesIfEdited() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  const valuesA = sheet.getRange("A2:A" + lastRow).getValues();

  for (let i = 0; i < valuesA.length; i++) {
    const cellContent = valuesA[i][0];
    const checkboxCell = sheet.getRange(i + 2, 6); // F
    if (cellContent !== "") {
      if (!checkboxCell.getDataValidation()) checkboxCell.insertCheckboxes();
    } else {
      checkboxCell.clearContent();
      checkboxCell.removeCheckboxes();
    }
  }
}

/***********************
 * MANUAL WIDTH UPDATES
 ***********************/
function updateJPWidths() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  const jpValues = sheet.getRange("A2:A" + lastRow).getValues();
  const jpWidths = jpValues.map(r => r[0] ? [calculateWidth(r[0])] : [""]);
  sheet.getRange("J2:J" + lastRow).setValues(jpWidths);
  SpreadsheetApp.getActive().toast("JP Widths updated (A → J)", "Width Tools", 3);
}

function updateENWidths() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  const enValues = sheet.getRange("B2:B" + lastRow).getValues();
  const enWidths = enValues.map(r => r[0] ? [calculateWidth(r[0])] : [""]);
  sheet.getRange("K2:K" + lastRow).setValues(enWidths);
  SpreadsheetApp.getActive().toast("EN Widths updated (B → K)", "Width Tools", 3);
}

function updateFinalWidthsFromC() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  const finalValues = sheet.getRange("C2:C" + lastRow).getValues();
  const finalWidths = finalValues.map(r => r[0] ? [calculateWidth(r[0])] : [""]);
  sheet.getRange("L2:L" + lastRow).setValues(finalWidths);
  SpreadsheetApp.getActive().toast("Final Widths updated (C → L)", "Width Tools", 3);
}
