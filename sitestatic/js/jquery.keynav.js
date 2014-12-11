/*
Copyright (c) 2012

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

$.fn.keynav = (function () {
	//a couple of global things for the plugin
	var nodes = $(), moving = false, positions = [], recalculate_positions, params;
	params = {
		speed: 150,
		scrolltreshold: 60,
		keynext: 74,
		keyprev: 75
	};
	//we're watching keypresses globally as well.
	$(document).keydown(function(e) {
		var st, prev, next, desired, i;
		if (!nodes.length) {return true;}
		if (moving) {return true;}
		if (e.target && e.target.tagName == 'TEXTAREA' || e.target.tagName == 'INPUT') {
			return true;
		}
		if(e.keyCode == params.keynext || e.keyCode == params.keyprev) {
			st = $(window).scrollTop();
			//we're checking if our positions are still correct. it may not be necessary all the time, but just to be safe
			if(positions[positions.length-1].top !== $(positions[positions.length-1].obj).offset().top) {
				recalculate_positions();
			}
			
			if(e.keyCode === params.keynext) {
				for(i = 0; i < positions.length; i++) {
					if(positions[i].top > st + 1) {desired = i; break;}
				}
			} else if(e.keyCode === params.keyprev) {
				for(i = 0; i < positions.length; i++) {
					if(positions[i].top < st - 1) {desired = i;}
				}
			}
			moving = true;
			if(positions[desired]) {
				$('html,body').animate({'scrollTop': positions[desired].top}, Math.abs(positions[desired].top - st) > params.scrolltreshold ? params.speed : 0, function() {moving = false;});
			} else {
				$('html,body').animate({'scrollTop': (e.keyCode === params.keynext ? ($('body').height() - $(window).height()) : 0)}, params.speed,	 function() {moving = false;});
			}
		}
	});
	
	recalculate_positions = function () {
		//this recalculates the positions of nodes
		positions = [];
		nodes.each(function() {
			positions.push({top: Math.floor($(this).offset().top),obj: this});
		});
	};
	
	return function(newparams) {
		//all we do in the actual plugin is we take the parameters and add the new nodes where we want to navigate.
		params = $.extend(params,newparams || {});
		nodes = nodes.add(this);
		recalculate_positions();
	};
	
})();
