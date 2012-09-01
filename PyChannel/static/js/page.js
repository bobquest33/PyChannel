$(document).ready(function () {
	$(".image img").live("click", function () {
		$(this).toggleImage();
	});
	
	$(".expand-images").live("click", function () {
		$("#op[threadid="+ $(this).attr("threadid") +"] .image img").toggleImage();
		$(".reply[threadid="+ $(this).attr("threadid") +"] .reply-container .image img").each(function () {
			$(this).toggleImage();
		});
	});
	
});