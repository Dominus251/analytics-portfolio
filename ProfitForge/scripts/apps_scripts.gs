function onEdit(e) {
  var sheet = e.source.getActiveSheet();
  var range = e.range;
  
  // НАСТРОЙКА: Название вашего листа (замените "Inputs", если оно другое)
  var targetSheet = "Inputs"; 
  
  // Ячейки B9:B11 — это строка от 9 до 11, столбец 2 (B)
  var startRow = 9;
  var endRow = 11;
  var col = 2; 
  
  // Проверяем, что изменен именно диапазон B9:B11 на нужном листе
  if (sheet.getName() === targetSheet && range.getColumn() === col && range.getRow() >= startRow && range.getRow() <= endRow) {
    var editedRow = range.getRow();
    var newValue = e.value ? parseFloat(e.value) : 0;
    
    // Ограничиваем ввод от 0 до 100
    if (newValue < 0) newValue = 0;
    if (newValue > 100) newValue = 100;
    
    // Находим строки двух других элементов
    var otherRows = [];
    for (var r = startRow; r <= endRow; r++) {
      if (r !== editedRow) otherRows.push(r);
    }
    
    var row1 = otherRows[0];
    var row2 = otherRows[1];
    
    // Считываем их текущие значения
    var val1 = sheet.getRange(row1, col).getValue() || 0;
    var val2 = sheet.getRange(row2, col).getValue() || 0;
    var currentSumOfOthers = val1 + val2;
    
    // Сколько процентов осталось распределить
    var remaining = 100 - newValue;
    var newVal1, newVal2;
    
    if (currentSumOfOthers > 0) {
      // Пропорционально уменьшаем/увеличиваем остальные ячейки
      newVal1 = (val1 / currentSumOfOthers) * remaining;
      newVal2 = (val2 / currentSumOfOthers) * remaining;
    } else {
      // Если остальные были по 0, делим остаток поровну
      newVal1 = remaining / 2;
      newVal2 = remaining / 2;
    }
    
    // Записываем округленные до целых или сотых значения (здесь до 2 знаков для точности)
    sheet.getRange(row1, col).setValue(Math.round(newVal1 * 100) / 100);
    sheet.getRange(row2, col).setValue(Math.round(newVal2 * 100) / 100);
    sheet.getRange(editedRow, col).setValue(newValue);
  }
}
