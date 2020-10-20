var myphotos = function () {

  var BASE_URL = 'https://cmp.photoprintit.com/api/2.0/api';  // Live System
  // var BASE_URL = 'https://opstest.photoprintit.com/api/2.0/api'; // Test system
  var API_ACCESS_KEY = 'f41756afefefec99d9e5064ca02000ad'; // ops-script
  var CLIENT_VERSION = '0.0.0-classification-demo';
  var PHOTO_COUNT = 100;
  var THUMB_SIZE = 'minHeight100';

  /**
   * Renders the main html elements into the root html element referenced by the given id
   * @param rootElementId the html element id to render the content into
   */
  var renderMainContent = function(rootElementId) {
    $('#' + rootElementId).empty().append($(
        '<div>'
      + '  <h2>Welcome to CEWE MYPHOTOS<span id="cmpLoginState"></span></h2>'
      + '  <form id="cmpLoginForm" class="form-inline">'
      + '    <div class="form-group">'
      + '      <label for="cmpEmail">Email</label>'
      + '      <input type="text" class="form-control" id="cmpEmail" placeholder="max.mustermann@gmail.com">'
      + '    </div>'
      + '    <div class="form-group">'
      + '      <label for="cmpPassword">Password</label>'
      + '      <input type="password" class="form-control" id="cmpPassword">'
      + '    </div>'
      + '    <button type="button" class="btn btn-primary" id="cmpLoginBtn">'
      + '      <span class="glyphicon glyphicon-log-in"> Login</span>'
      + '    </button>'
      + '  </form>'
      + '  <div id="cmpContentArea" style="display:none">'
      + '    <h3>Try an action!</h3>'
      + '    <div class="btn-group">'
      + '     <button id="cmpGoodLuckBtn" class="btn btn-primary">Good Luck!</button>'
      + '     <button id="cmpEventsBtn" class="btn btn-default">Load Events</button>'
      + '     <button id="cmpLogoutBtn" class="btn btn-danger">Logout</button>'
      + '    </div>'
      + '    <div id="cmpContent">'
      + '      <div id="cmpEvents"></div>'
      + '      <div id="cmpPhotos"></div>'
      + '    </div>'
      + '  </div>'
      + '</div>'
    ));
  };

  /**
   * Resets the content divs (photos and events)
   */
  var resetContent = function() {
    $('#cmpEvents').empty();
    $('#cmpPhotos').empty();
  };

  /**
   * @returns the sessionInfo from sessionStorage or null
   */
  var getSessionInfo = function() {
    return sessionStorage.cmpSession ? JSON.parse(sessionStorage.cmpSession) : null;
  };

  /**
   * Unsets the sessionInfo in the sessionStorage
   */
  var unsetSessionInfo = function () {
    delete sessionStorage.cmpSession;
    console.log('Successfully logged out from CEWE MYPHOTOS.');
    updateLogin();
  };

  /**
   * Updates the view by toggling the login form and the content area
   */
  var updateLogin = function () {
    var sessionInfo = getSessionInfo();
    if (sessionInfo) {
      $('#cmpLoginState').text(', you are logged in as ' + sessionInfo.user.firstname + ' ' + sessionInfo.user.lastname);
      $('#cmpLoginForm').hide();
      $('#cmpContentArea').show();
    } else {
      $('#cmpLoginState').text(', please enter your credentials and login');
      $('#cmpContentArea').hide();
      $('#cmpLoginForm').show();
      resetContent();
    }
  };

  /**
   * Login to CEWE MYPHOTOS with the given credentials
   *
   * @param email the mail of the registered user
   * @param password the plain password
   */
  var login = function (email, password) {
    console.log('Perform login to CEWE MYPHOTOS for login "' + email + '.');
    var setSessionInfo = function (data) {
      sessionStorage.cmpSession = JSON.stringify(data);
      console.log('Successfully logged in to CEWE MYPHOTOS, new session id "' + data.session.cldId + '.');
      updateLogin();
    };
    request('/account/session', setSessionInfo, { method: 'POST', data: { login: email, password: password, deviceName: 'Classification Demo via Browser' } });
  };

  /**
   * Logout of the currently used session
   */
  var logout = function() {
    request('/account/session', unsetSessionInfo, { method: 'DELETE', cldId: getSessionInfo().session.cldId });
  };

  /**
   * Fetches photos of the currently logged in user. If the event is set, up to 999 photos will be loaded from
   * the given event. If not set PHOTO_COUNT (100) random photos will be loaded from the user account.
   * @param event of the photos, can be undefined
   */
  var loadPhotos = function (event) {
    resetContent();

    var photoFromEvent = event !== undefined;
    var renderPhotos = function (data) {
      var title = photoFromEvent
        ? data.photos.length + ' Photos from event <b>' + (event.name !== undefined ? event.name : formatDate(new Date(event.startDate))) + '</b>'
        : data.photos.length + ' random photos';
      $('#cmpPhotos').append($('<h3>' + title + '</h3><p>Click on a photo to download it.</p>'));
	$.each(data.photos, function (index, photo) {
            var imgUrl = BASE_URL + '/photos/' + photo.id + '.jpg?size=' + THUMB_SIZE + '&cldId=' + getSessionInfo().session.cldId + '&clientVersion=' + CLIENT_VERSION;
            var downloadUrl = BASE_URL + '/photos/' + photo.id + '.jpg?size=download&cldId=' + getSessionInfo().session.cldId + '&clientVersion=' + CLIENT_VERSION;
            // Use the download url to get the jpeg-images for your classification.
            // Notice as 'size' you can use 100, 300, 720, 1000, 1280, 2000, minHeight100, minHeight300, download.
            // 'download' means full-resolution.
	   
	    
             $('#cmpPhotos').append($(
              '<div class="col-sm-2">'
		  + '  <a href="' + downloadUrl + '">'
		  + '    <div id="img-' + photo.id + '" class="thumbnail">'
		  + '      <img src="' + imgUrl + '" alt="' + photo.title + '" />'
		  + '      <div class="text-center">' + abbreviate(photo.name, 15) + '</div>'
		  + '    </div>'
		  + '  </a>'
		  + '</div>'
             ));
	    //larbi 16.06.2017 redirect the download url to the classification based on url "classify_url" code from Albert
	    $('#' + photo.id).click(function () {
		var posting = $.post("classify_url", {
                    imageurl: downloadUrl,
                    //username: "{{ username }}",
                    //places: places,
                    //multi: multi,
                    ImageNet_VGG_S: ImageNet_VGG_S,
                    style: style
		});
		//posting.done(function () {
	//	    index += 1;
		  //  $('#cmpPhotos').empty().append($('<h3>picture '+ index +' is done</h3>'));
	    });
	});
    };
      
	       
    var url = photoFromEvent
      ? '/photoEvents/' + event.id + '/photos?pageSize=999'
      : '/photos/shuffle?photoCount=' + PHOTO_COUNT;

    request(url, renderPhotos, { cldId: getSessionInfo().session.cldId });
  };

  /**
   * Fetches the events of the currently logged in user.
   */
  var loadEvents = function () {
    resetContent();

    var renderEvents = function (data) {
      $('#cmpEvents').append($('<h3>Events</h3><p>Select an event by clicking the photo.</p>'));
      $.each(data.albums, function (index, event) {
        var coverPhotoId = event.coverPhotoId || event.photoIds[0];
        var coverUrl = BASE_URL + '/photos/' + coverPhotoId + '.jpg?size=' + THUMB_SIZE + '&cldId=' + getSessionInfo().session.cldId + '&clientVersion=' + CLIENT_VERSION;
        var caption = (event.name !== undefined ? event.name : formatDate(new Date(event.startDate))) + ' (' + event.photoCount + ')';
        $('#cmpEvents').append($(
              '<div class="col-sm-2">'
            + '  <div id="event-' + event.id + '" class="thumbnail">'
            + '    <img src="' + coverUrl + '" alt="' + event.name + '" />'
            + '    <div class="text-center">' + caption + '</div>'
            + '  </div>'
            + '</div>'));
        $('#event-' + event.id).click(function() {
          loadPhotos(event);
        })
      });
    };

    request('/photoEvents?representatives=1', renderEvents, { cldId: getSessionInfo().session.cldId });
  };

  /**
   * Performs the GET requests to CEWE MYPHOTOS API
   *
   * @param resource appended to BASE_URL
   * @param successCallback the callback method called after request success, first parameter will be the json
   *        data got from the server
   * @param config optional config (attr: method, data, cldId
   */
  var request = function(resource, successCallback, config) {
    config = config || {};
    var headers = { 'clientVersion': CLIENT_VERSION };
    if (config.cldId === undefined) {
      headers.apiAccessKey = API_ACCESS_KEY;
    } else {
      headers.cldId = config.cldId;
    }

    $.ajax({
      url: BASE_URL + resource,
      method: config.method || 'GET',
      data : config.data !== undefined ? JSON.stringify(config.data) : undefined,
      dataType: 'json',
      contentType: 'application/json',
      headers: headers,
      success: successCallback,
      error: function (data) {
        alert('Unable to connect, unset session info. From server: ' + JSON.stringify(data));
        unsetSessionInfo();
        updateLogin();
      }
    })
  };

  /**
   * Formats the given date to dd.mm.yyyy
   * @param date the date to format
   * @returns the formated string
   */
  var formatDate = function(date) {
    var toStr = function(i) {
      return (i < 10 ? '0' : '') + i;
    };
    var day = toStr(date.getDate());
    var month = toStr(date.getMonth() + 1);
    var year = toStr(date.getFullYear());
    return day + ' ' + month + ' ' + year;
  };

  /**
   * Abbreviates the given string to the given length
   * @param str the string to abbreviate
   * @returns the abbreviates string
   */
  var abbreviate = function(str, length) {
    return str.length > length ? str.substr(0, length - 3) + '...' : str;
  };

  return {
    /**
     * Initializes the CEWE MYPHOTOS content
     * @param rootElementId the id of the root html element to render content into.
     */
    init: function (rootElementId) {
      renderMainContent(rootElementId);

      $('#cmpLoginBtn').click(function () {
        login($('#cmpEmail').val(), $('#cmpPassword').val());
      });

      $('#cmpLogoutBtn').click(function () {
        logout();
      });

      $('#cmpGoodLuckBtn').click(function () {
        loadPhotos();
      });

      $('#cmpEventsBtn').click(function () {
        loadEvents();
      });

      updateLogin();
      console.log('CEWE MYPHOTOS initialized.');
    }
  };
}();
myphotos.init('cmpRoot');
