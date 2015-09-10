$(document).ready(function () {
    $('.oe_website_sale').each(function () {
        var oe_website_sale = this;
        $(oe_website_sale).off("change", ".oe_cart input.js_quantity").on("change", ".oe_cart input.js_quantity", function (event) {
            var $input = $(this);
            var value = parseInt($input.val(), 10);
            var $dom = $(event.target).closest('tr');
            var default_price = parseFloat($dom.find('.text-danger > span.oe_currency_value').text().replace(',','.'));
            var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
            var line_id = parseInt($input.data('line-id'),10);
            var product_id = parseInt($input.data('product-id'),10);
            var product_ids = [product_id];
            $dom_optional.each(function(){
                product_ids.push($(this).find('span[data-product-id]').data('product-id'));
            });
            if (isNaN(value)) value = 0;
            openerp.jsonRpc("/shop/get_unit_price", 'call', {
                'product_ids': product_ids,
                'add_qty': value})
            .then(function (res) {
                //basic case
                $dom.find('span.oe_currency_value').last().text(res[product_id].toFixed(2));
                $dom.find('.text-danger').toggle(res[product_id]<default_price && (default_price-res[product_id] > default_price/1000));
                //optional case
                $dom_optional.each(function(){
                    var id = $(this).find('span[data-product-id]').data('product-id');
                    var price = parseFloat($(this).find(".text-danger > span.oe_currency_value").text().replace(',','.'));
                    $(this).find("span.oe_currency_value").last().text(res[id].toFixed(2));
                    $(this).find('.text-danger').toggle(res[id]<price && (price-res[id]>price/1000));
                });
                openerp.jsonRpc("/shop/cart/update_json", 'call', {
                'line_id': line_id,
                'product_id': parseInt($input.data('product-id'),10),
                'set_qty': value})
                .then(function (data) {
                    if (!data.quantity) {
                        location.reload();
                        return;
                    }
                    var $q = $(".my_cart_quantity");
                    $q.parent().parent().removeClass("hidden", !data.quantity);
                    $q.html(data.cart_quantity).hide().fadeIn(600);

                    $input.val(data.quantity);
                    $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);
                    $("#cart_total").replaceWith(data['website_sale.total']);
                });
            });
        });

        function price_to_str(price) {
            price = Math.round(price * 100) / 100;
            var dec = Math.round((price % 1) * 100);
            return price + (dec ? '' : '.0') + (dec%10 ? '' : '0');
        }
        
        $(oe_website_sale).off('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]').on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function (ev) {
            var $ul = $(ev.target).closest('ul.js_add_cart_variants');
            var $parent = $ul.closest('.js_product');
            var $product_id = $parent.find('input.product_id').first();
            var $price = $parent.find(".oe_price:first .oe_currency_value");
            var $default_price = $parent.find(".oe_default_price:first .oe_currency_value");
            var $optional_price = $parent.find(".oe_optional:first .oe_currency_value");
            var variant_ids = $ul.data("attribute_value_ids");
            var values = [];
            $parent.find('input.js_variant_change:checked, select.js_variant_change').each(function () {
                values.push(+$(this).val());
            });

            $parent.find("label").removeClass("text-muted css_not_available");

            var product_id = false;
            for (var k in variant_ids) {
                if (_.isEmpty(_.difference(variant_ids[k][1], values))) {
                    $price.html(price_to_str(variant_ids[k][2]));
                    $default_price.html(price_to_str(variant_ids[k][3]));
                    if (variant_ids[k][3]-variant_ids[k][2]>0.01) {
                        $default_price.closest('.oe_website_sale').addClass("discount");
                        $optional_price.closest('.oe_optional').show().css('text-decoration', 'line-through');
                    } else {
                        $default_price.closest('.oe_website_sale').removeClass("discount");
                        $optional_price.closest('.oe_optional').hide();
                    }
                    product_id = variant_ids[k][0];
                    break;
                }
            }

            if (product_id) {
                var $img = $(this).closest('tr.js_product, .oe_website_sale').find('span[data-oe-model^="product."][data-oe-type="image"] img:first, img.product_detail_img');
                $img.attr("src", "/website/image/product.product/" + product_id + "/image");
                $img.parent().attr('data-oe-model', 'product.product').attr('data-oe-id', product_id)
                    .data('oe-model', 'product.product').data('oe-id', product_id);
            }

            $parent.find("input.js_variant_change:radio, select.js_variant_change").each(function () {
                var $input = $(this);
                var id = +$input.val();
                var values = [id];

                $parent.find("ul:not(:has(input.js_variant_change[value='" + id + "'])) input.js_variant_change:checked, select").each(function () {
                    values.push(+$(this).val());
                });

                for (var k in variant_ids) {
                    if (!_.difference(values, variant_ids[k][1]).length) {
                        return;
                    }
                }
                $input.closest("label").addClass("css_not_available");
                $input.find("option[value='" + id + "']").addClass("css_not_available");
            });

            if (product_id) {
                $parent.removeClass("css_not_available");
                $product_id.val(product_id);
                $parent.find(".js_check_product").removeAttr("disabled");
            } else {
                $parent.addClass("css_not_available");
                $product_id.val(0);
                $parent.find(".js_check_product").attr("disabled", "disabled");
            }
        });
        $('ul.js_add_cart_variants', oe_website_sale).each(function () {
            $('input.js_variant_change, select.js_variant_change', this).first().trigger('change');
        });

    });
});
