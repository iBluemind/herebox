var allGoogleMaps = {};

function initIUGoogleMap(iu){
	
	//style
	var styleIndex = parseInt( $(iu).attr('themeType') );
	var style;
	if(styleIndex > 0){
		style = dictionaryForIUGoogleMapThemeIndex(styleIndex-1);
	}
	
	//option
	var latitude = parseFloat( $(iu).attr('latitude') );
	var longitude = parseFloat( $(iu).attr('longitude') );
	var zoomLevel = parseInt( $(iu).attr('zoom') );
	var zoomControl = $(iu).attr('zoomControl') == 'true';
	var streetControl = $(iu).attr('streetControl') == 'true';
	var option = {
		center : new google.maps.LatLng(latitude, longitude),
		zoom : zoomLevel,
		zoomControl : zoomControl,
		streetViewControl : streetControl,
		mapTypeControl : false,
		styles : style
	};
	
	//create map
	var map = new google.maps.Map(iu, option);
	
	//add marker icon
	var markerIcon = $(iu).attr('markerIcon') == 'true';
	if (markerIcon){
		var iconImagePath = $(iu).attr('markerIconPath');
		var marker;
		if (iconImagePath != undefined){
			marker = new google.maps.Marker({
				map : map,
				position :map.getCenter(),
				icon : iconImagePath
			});
		}
		else{
			marker = new google.maps.Marker({
				map : map,
				position :map.getCenter()
			});
		}
	
		//click infomation
		var title = $(iu).attr('markerTitle');
		if (title != undefined){
			var infoWindow = new google.maps.InfoWindow();
			infoWindow.setContent('<p>'+title+'</p>');
			google.maps.event.addListener(marker, 'click', function(){
				infoWindow.open(map, marker);
			});
		}
	}
	
	//add event listner : (resize)
	google.maps.event.addListener(window, "resize", function(){
		var center = new google.maps.LatLng(latitude, longitude);
		google.maps.event.trigger(map, "resize");
		map.setCenter(center);
	});	
	
	$(iu).data('googleMap', map);
}

function resizeIUGoogleMap(iu){
	var latitude = parseFloat( $(iu).attr('latitude') );
	var longitude = parseFloat( $(iu).attr('longitude') );
	var map = $(iu).data('googleMap');
	var center = new google.maps.LatLng(latitude, longitude);
	google.maps.event.trigger(map, "resize");
	map.setCenter(center);
}



function dictionaryForIUGoogleMapThemeIndex(index){
	var themeList = [
	//paledawn-start
	[{"featureType":"water","stylers":[{"visibility":"on"},{"color":"#acbcc9"}]},{"featureType":"landscape","stylers":[{"color":"#f2e5d4"}]},{"featureType":"road.highway","elementType":"geometry","stylers":[{"color":"#c5c6c6"}]},{"featureType":"road.arterial","elementType":"geometry","stylers":[{"color":"#e4d7c6"}]},{"featureType":"road.local","elementType":"geometry","stylers":[{"color":"#fbfaf7"}]},{"featureType":"poi.park","elementType":"geometry","stylers":[{"color":"#c5dac6"}]},{"featureType":"administrative","stylers":[{"visibility":"on"},{"lightness":33}]},{"featureType":"road"},{"featureType":"poi.park","elementType":"labels","stylers":[{"visibility":"on"},{"lightness":20}]},{},{"featureType":"road","stylers":[{"lightness":20}]}]
	//paledawn-end
	,
	//subtlegrayscale-start
	[{"featureType":"landscape","stylers":[{"saturation":-100},{"lightness":65},{"visibility":"on"}]},{"featureType":"poi","stylers":[{"saturation":-100},{"lightness":51},{"visibility":"simplified"}]},{"featureType":"road.highway","stylers":[{"saturation":-100},{"visibility":"simplified"}]},{"featureType":"road.arterial","stylers":[{"saturation":-100},{"lightness":30},{"visibility":"on"}]},{"featureType":"road.local","stylers":[{"saturation":-100},{"lightness":40},{"visibility":"on"}]},{"featureType":"transit","stylers":[{"saturation":-100},{"visibility":"simplified"}]},{"featureType":"administrative.province","stylers":[{"visibility":"off"}]},{"featureType":"water","elementType":"labels","stylers":[{"visibility":"on"},{"lightness":-25},{"saturation":-100}]},{"featureType":"water","elementType":"geometry","stylers":[{"hue":"#ffff00"},{"lightness":-25},{"saturation":-97}]}]	
	//subtlegrayscale-end
	,
	//bluegray-start
	[{"featureType":"water","stylers":[{"visibility":"on"},{"color":"#b5cbe4"}]},{"featureType":"landscape","stylers":[{"color":"#efefef"}]},{"featureType":"road.highway","elementType":"geometry","stylers":[{"color":"#83a5b0"}]},{"featureType":"road.arterial","elementType":"geometry","stylers":[{"color":"#bdcdd3"}]},{"featureType":"road.local","elementType":"geometry","stylers":[{"color":"#ffffff"}]},{"featureType":"poi.park","elementType":"geometry","stylers":[{"color":"#e3eed3"}]},{"featureType":"administrative","stylers":[{"visibility":"on"},{"lightness":33}]},{"featureType":"road"},{"featureType":"poi.park","elementType":"labels","stylers":[{"visibility":"on"},{"lightness":20}]},{},{"featureType":"road","stylers":[{"lightness":20}]}]
	//bluegray-end
	,
	//green-start
	[{"featureType":"landscape","elementType":"geometry.fill","stylers":[{"color":"#bbd5c5"}]},{"featureType":"road.local","elementType":"geometry.stroke","stylers":[{"color":"#808080"}]},{"featureType":"road.highway","elementType":"geometry.fill","stylers":[{"color":"#fcf9a2"}]},{"featureType":"poi","elementType":"geometry.fill","stylers":[{"color":"#bbd5c5"}]},{"featureType":"road.highway","elementType":"geometry.stroke","stylers":[{"color":"#808080"}]}]
	//green-end
	];
	
	return themeList[index];
}