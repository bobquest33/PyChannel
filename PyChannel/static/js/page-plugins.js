(function ($) {
	
	$.fn.toggleImage = function (speed) {
		image_id = $(this).attr("src").match(/[0-9]+?/)[0];
		extension = $(this).attr("src").substring($(this).attr("src").lastIndexOf("."))
		
		if ($(this).attr("src").match(/thumb/)) {
			$(this).attr("src","/images/"+image_id+extension);
		} else {
			$(this).attr("src","/images/thumb."+image_id+extension);
		}
	}
	
})(jQuery)