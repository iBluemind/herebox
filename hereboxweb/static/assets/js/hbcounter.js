function HereboxCounter (btnSubtract, btnAdd, divCountItem, callback) {
    this.btnSubtract = btnSubtract;
    this.btnAdd = btnAdd;

    this.btnSubtract.click(function() {
        var itemNumber = Number(divCountItem.text());
        if (itemNumber > 0) {
            itemNumber = itemNumber - 1;
        }
        divCountItem.text(itemNumber);
        if (callback) {
            callback('subtract', itemNumber);
        }
    });

    this.btnAdd.click(function() {
        var itemNumber = Number(divCountItem.text());
        itemNumber = itemNumber + 1;
        divCountItem.text(itemNumber);
        if (callback) {
            callback('add', itemNumber);
        }
    });
}
