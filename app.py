/**
 * 【doGet】Streamlitアプリがデータを読み込む際に呼び出される関数
 * スプレッドシートのデータをそのままJSON形式で返す（並び替えもしない）
 */
function doGet() {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = sheet.getDataRange().getValues();
    
    // データがない場合は空配列を返す
    if (data.length <= 1) {
      return ContentService.createTextOutput(JSON.stringify([])).setMimeType(ContentService.MimeType.JSON);
    }
    
    // 1行目はヘッダー
    var body = data.slice(1);
    
    // データをJSON化（日付はそのまま文字列として送る）
    var result = body.map(function(row) {
      // 空白行はスキップ
      if (!row[0]) return null;
      return {
        date: String(row[0]), // 比較用に文字列化
        content: String(row[2]) // 本文
      };
    }).filter(function(item) { return item !== null; });
    
    return ContentService.createTextOutput(JSON.stringify(result)).setMimeType(ContentService.MimeType.JSON);
    
  } catch (e) {
    return ContentService.createTextOutput(JSON.stringify({error: e.toString()})).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * 【doPost】Streamlitアプリがデータを保存する際に呼び出される関数
 * 指定された日付の行を探して上書き、なければ追加する（全消ししない）
 */
function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // アプリから送られてきたデータを解析
    var params = JSON.parse(e.postData.contents);
    var targetDateStr = String(params.date); // 比較用（例: "2024-06-22"）
    
    // A列（日付）のデータだけを全部取得（本文は取得しないので速い）
    var lastRow = sheet.getLastRow();
    
    // データが1行もない場合（ヘッダーのみ）
    if (lastRow <= 1) {
      sheet.appendRow([params.date, params.header, params.content]);
      return ContentService.createTextOutput("Added (First)");
    }
    
    var dateRange = sheet.getRange(2, 1, lastRow - 1, 1);
    var dateValues = dateRange.getValues(); // A列の値の配列
    
    // 指定した日付の行があるか探す
    var foundRow = -1;
    for (var i = 0; i < dateValues.length; i++) {
      var currentRowDate = dateValues[i][0];
      
      // 日付の表記揺れ（スラッシュ、ハイフン、日本語）を簡易的に統一して比較
      var normCurrentRow = String(currentRowDate).replace(/\//g, '-').replace(/[年Wait]/g, '-').replace(/日/g, '').split(' ')[0].split('（')[0];
      var normTarget = targetDateStr.replace(/\//g, '-');

      if (normCurrentRow === normTarget) {
        foundRow = i + 2; // 行番号を取得（indexは0始まり、ヘッダー分で+2）
        break;
      }
    }
    
    if (foundRow !== -1) {
      // 見つかった場合：その行のC列（本文）だけを上書き（一番軽量）
      sheet.getRange(foundRow, 3).setValue(params.content);
      // B列（ヘッダー）も念のため更新
      sheet.getRange(foundRow, 2).setValue(params.header);
      return ContentService.createTextOutput("Updated Row: " + foundRow);
    } else {
      // 見つからなかった場合：一番下に追加
      sheet.appendRow([params.date, params.header, params.content]);
      return ContentService.createTextOutput("Added to Bottom");
    }
    
  } catch (e) {
    // エラー発生時はエラーメッセージを返す
    return ContentService.createTextOutput("Error: " + e.toString());
  }
}
