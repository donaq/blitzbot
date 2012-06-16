var x1=-1;
var y1=-1;
var x2=-1;
var y2=-1;
count = 0;
var overlayshown = false;
$(document).ready(function(){
	$('body').append('<div id="debug" />');
	$('body').append('<div id="overlay" />');
	$(document).keypress(function(evt){
		if(evt.which==106){
			if(!overlayshown){
				$("#overlay").show().css({
					"position":"absolute",
					"top":0,
					"left":0,
					"opacity":0.5,
					"zIndex":10000,
					"backgroundColor": "#FFFFFF"
				}).height($(document).height()).width($(document).width());
				overlayshown = true;
			}
			else{
				$("#overlay").hide();
				overlayshown = false;
				if(x1==-1||x2==-1||y2==-1||y1==-1) return;
				$.post("http://localhost:9999", {"coords":[x1,y1,x2,y2].join(' ')});
				x1 = y1 = x2 = y2 = -1;
			}
		}
	});
	$(document).click(function(evt){
		if(!overlayshown) return;
		$("#overlay").html('coords');
		if(x1==-1){
			$("#overlay").html('coords '+evt.screenX+' '+evt.screenY);
			x1 = evt.screenX;
			y1 = evt.screenY;
		}
		else if(x2==-1){
			x2 = evt.screenX;
			y2 = evt.screenY;
		}
	});
});
