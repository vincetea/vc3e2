/***********************
 * WIDTH CALCULATION
 ***********************/
function calculateWidth(cellValue) {
  if (!cellValue) return "";

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

  return cellValue.toString().split(/\r?\n/).map(line => {
    let total = 0;
    for (let ch of line) {
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
  if (row <= 1) return;

  // Column B → JP width (K) + checkbox H
  if (col === 2) {
    const val = e.range.getValue();
    sheet.getRange(row, 11).setValue(val ? calculateWidth(val) : "");
  }

  // Column C → copy to D + EN width (L) + Final width (M)
  if (col === 3) {
    const val = e.range.getValue();

    sheet.getRange(row, 4).setValue(val);
    sheet.getRange(row, 12).setValue(val ? calculateWidth(val) : "");
    sheet.getRange(row, 13).setValue(val ? calculateWidth(val) : "");

    const checkbox = sheet.getRange(row, 8);
    if (val !== "") {
      if (!checkbox.getDataValidation()) checkbox.insertCheckboxes();
    } else {
      checkbox.clearContent();
      checkbox.removeCheckboxes();
    }
  }

  // Column D → Final width only (M)
  if (col === 4) {
    const val = e.range.getValue();
    sheet.getRange(row, 13).setValue(val ? calculateWidth(val) : "");
  }
}

/***********************
 * MENU
 ***********************/
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("Width & Approved Tools")
    .addItem("✔️ Check All Approved (H)", "checkAllReviewed")
    .addItem("❌ Uncheck All Approved (H)", "uncheckAllReviewed")
    .addSeparator()
    .addItem("☑️ Add approved? checkboxes (B → H)", "addCheckboxesBasedOnBtoH")
    .addItem("☑️ Add work on checkboxes (B → A)", "addCheckboxesBasedOnB")
    .addSeparator()
    .addItem("🖊 Update JP Widths (B → K)", "updateJPWidths")
    .addItem("🖊 Update EN Widths (C → L)", "updateENWidths")
    .addItem("🖊 Update Final Widths (D → M)", "updateFinalWidths")
    .addToUi();
}

/***********************
 * CHECKBOX HELPERS (COLUMN H)
 ***********************/
function checkAllReviewed() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  const values = sheet.getRange("B2:B" + lastRow).getValues();
  sheet.getRange("H2:H" + lastRow).setValues(values.map(r => [r[0] !== ""]));
}

function uncheckAllReviewed() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  sheet.getRange("H2:H" + lastRow).setValues(Array(lastRow - 1).fill([false]));
}

/***********************
 * MANUAL WIDTH UPDATES
 ***********************/
function updateJPWidths() {
  bulkUpdate("B", "K");
}

function updateENWidths() {
  bulkUpdate("C", "L");
}

function updateFinalWidths() {
  bulkUpdate("D", "M");
}

function bulkUpdate(fromCol, toCol) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  const values = sheet.getRange(`${fromCol}2:${fromCol}${lastRow}`).getValues();
  sheet.getRange(`${toCol}2:${toCol}${lastRow}`)
    .setValues(values.map(r => [r[0] ? calculateWidth(r[0]) : ""]));
}

/***********************
 * MANUAL CHECKBOX (B → H)
 ***********************/
function addCheckboxesBasedOnBtoH() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  const valuesB = sheet.getRange("B2:B" + lastRow).getValues();

  for (let i = 0; i < valuesB.length; i++) {
    const cellContent = valuesB[i][0];
    const checkboxCell = sheet.getRange(i + 2, 8); // H

    if (cellContent !== "") {
      if (!checkboxCell.getDataValidation()) {
        checkboxCell.insertCheckboxes();
      }
    } else {
      checkboxCell.clearContent();
      checkboxCell.removeCheckboxes();
    }
  }
}

/***********************
 * LEGACY FUNCTION (UNCHANGED)
 ***********************/
// Add checkboxes in Column A if Column B is non-empty
function addCheckboxesBasedOnB() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow = sheet.getLastRow();
  const valuesB = sheet.getRange("B2:B" + lastRow).getValues();

  for (let i = 0; i < valuesB.length; i++) {
    const val = valuesB[i][0];
    const checkboxCell = sheet.getRange(i + 2, 1); // Column A

    if (val !== "") {
      if (checkboxCell.getDataValidation() == null) {
        checkboxCell.insertCheckboxes();
      }
    } else {
      checkboxCell.clearContent();
      checkboxCell.removeCheckboxes();
    }
  }
}
