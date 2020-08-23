$(document).ready(function() {
    var products_count = $("#products-table").attr('data-products-count');
    var users_count = $("#products-table").attr('data-users-count');

    function update() {
        var products_count = $("#products-table").attr('data-products-count');
        var total_price = $("#price").attr('data-total');
        var subtotal_price = $("#price").attr('data-subtotal');
        var bonus_factor = total_price / subtotal_price;
        var total_price_for_me = 0;

        for (i = 1; i < products_count + 1; i++) {
            var price = parseFloat($("#" + i + '-0').attr('data-price'));

            if ($("#" + i + '-0').is(":checked"))
                total_price_for_me += price * bonus_factor;
            else if ($("#" + i + '-2').is(":checked"))
                total_price_for_me += price / 2.0 * bonus_factor;
        }
        $("#price-me").text('Price for me: € ' + total_price_for_me.toFixed(2));
        $("#price-others").text('Price for the others: € ' + (total_price - total_price_for_me).toFixed(2));
    }

    for (i = 1; i < products_count + 1; i++) {
        for (j = 0; j < users_count; j++) {
            var id = "#" + i + '-' + j;
            $(id).click(function(event) {
                update();
            });
        }
    }
    update();
});
