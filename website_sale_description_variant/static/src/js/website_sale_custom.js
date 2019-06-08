odoo.define('website_sale_custom.website_sale', function (require) {
    "use strict";

    require('web.dom_ready');
    var base = require('web_editor.base');
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var time = require('web.time');
    var core = require('web.core');
    var config = require('web.config');
    var _t = core._t;
    
    if(!$('.oe_website_sale').length) {
        return $.Deferred().reject("DOM doesn't contain '.oe_website_sale'");
    }

    $('.oe_website_sale').each(function () {
        var oe_website_sale = this;

        $(oe_website_sale).on("change", "input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]", function (event) {
	        var $input = $(this);
	        var $ul = $(event.target).closest('.js_add_cart_variants');
	        var $parent = $ul.closest('.js_product');
	        var product_id = parseInt($parent.find('input.product_id').val());
	        var variant_ids = $ul.data("attribute_value_ids");
	        if(_.isString(variant_ids)) {
	            variant_ids = JSON.parse(variant_ids.replace(/'/g, '"'));
	        }
	        $(oe_website_sale).find('input.js_variant_change').parent('label').parent('li').show();
	        for (var k in variant_ids) {
	            if (variant_ids[k][0] != product_id) {
	                continue
	            }
	            var info = variant_ids[k][4];
	            var description = info.description_sale_variant || '';
	            $(oe_website_sale).find('#description_sale_variant').html(description);
	        }
	    });
    });
});
