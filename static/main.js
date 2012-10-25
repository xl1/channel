// Generated by CoffeeScript 1.3.3
(function() {
  var get, log, main, makeParam,
    __hasProp = {}.hasOwnProperty;

  makeParam = function(param) {
    var key, value;
    return ((function() {
      var _results;
      _results = [];
      for (key in param) {
        if (!__hasProp.call(param, key)) continue;
        value = param[key];
        _results.push("" + key + "=" + value);
      }
      return _results;
    })()).join('&');
  };

  get = function(url, param, callback) {
    var xhr;
    xhr = new XMLHttpRequest();
    xhr.open('GET', url + '?' + makeParam(param), true);
    xhr.onload = function() {
      return typeof callback === "function" ? callback(xhr.responseText) : void 0;
    };
    return xhr.send(null);
  };

  log = function(text) {
    var div;
    div = document.createElement('div');
    div.textContent = text;
    return document.body.appendChild(div);
  };

  main = function() {
    var channel, channelToken, id, socket, _ref;
    _ref = document.body.dataset, id = _ref.id, channelToken = _ref.channelToken;
    channel = new goog.appengine.Channel(channelToken);
    socket = channel.open();
    socket.onopen = function() {
      return log('open');
    };
    return socket.onmessage = function(e) {
      return log(e.data);
    };
  };

  main();

}).call(this);
