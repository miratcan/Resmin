/*
  TODO:
    * Check namings with javascript naming conventions.
    * Check for callback order.
    * Needs code review.
*/

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

var sliceMethod = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice;

function calculateMd5Sum(file, func, options) {
  var file = file;
  var offset = 0;
  var spark = new SparkMD5.ArrayBuffer();
  var options = _.extend({chunkSize: 1024 * 100,}, options || {});

  function readerOnLoad(ev) {
    spark.append(ev.target.result);
    if (offset >= file.size) {
      func(spark.end());
    } else {
      offset += options.chunkSize;
      loadChunk();      
    }
  };
  function readerOnError() {
    console.warn('something went wrong');
  };
  function loadChunk() {
    var fileReader = new FileReader();
    var start = offset;
    var end = ((start + options.chunkSize) >= file.size) ? file.size : start + options.chunkSize;
    fileReader.onload = readerOnLoad.bind(this);
    fileReader.onerror = readerOnError.bind(this);
    fileReader.readAsArrayBuffer(sliceMethod.call(file, start, end));
  };
  loadChunk();
};

function upload(file, upload_id, options) {
    var options = _.extend({
      'chunk_size': 1024 * 100,
      'url_prefix': '/upload/',
      onUploadComplete: function(result) {},
      onChunkSent: function(offset) {}
    }, options || {});
    var file_size = file.size;
    var upload_request = new XMLHttpRequest();
    function _contentRangeHeaderText(range_start, range_end) {
        return 'bytes ' + range_start + '-' + range_end + '/' + file_size
    };
    function _upload(range_start, range_end) {
      if (range_end > file_size) { range_end = file_size; };
      var chunk = file.slice(range_start, range_end);
      upload_request.open('PUT', options['url_prefix'] + upload_id + '/', true);
      upload_request.overrideMimeType('application/octet-stream');
      upload_request.setRequestHeader('Content-Range', _contentRangeHeaderText(range_start, range_end));
      upload_request.setRequestHeader("X-CSRFToken", csrftoken)
      upload_request.send(chunk);
    };
    upload_request.onreadystatechange = function() {
      if (upload_request.readyState == 4 && upload_request.status == 200) {
        var result = JSON.parse(upload_request.responseText);
        if (result.status == 'uploaded') {
          options['onUploadComplete'](result);
        } else {
          options['onChunkSent'](result.offset);
          var range_start = result.offset;
          var range_end = Math.min(file_size, range_start + options['chunk_size'])
          _upload(range_start, range_end);            
        }
      }
    }
    _upload(0, Math.min(options['chunk_size'], file_size));
};

function fileNameExt(filename) {
  var a = filename.split(".");
  if( a.length === 1 || ( a[0] === "" && a.length === 2 ) ) {
    return "";
  }
  return a.pop();  // feel free to tack .toLowerCase() here if you want};
};

function trimFileName(filename, ml, pl) {
  var ml = ml || 20;
  var pl = pl || 5;
  if (filename.length > ml) {
    var ext = fileNameExt(filename);
    var postfixLength = ext.length + pl
    var postfixStart = filename.length - postfixLength;
    var postfixEnd = filename.length;
    var prefixStart = 0;
    var prefixEnd = ml - (postfixLength + 3);
    return filename.slice(prefixStart, prefixEnd) + "..." + filename.slice(postfixStart, postfixEnd);
  } else {
    return filename;
  }
};

function updateOrders() {
  var order = 0;
  $('.order').each(function() {
    $(this).attr('value', order);
    order += 1;
  });
};

function getUpload(file, options) {
  var options = _.extend({
    getUploadURL: '/upload/',
    chunkSize: 1024 * 100,
    onUploadComplete: function(result) {},
    onChunkSent: function(offset) {}
  }, options || {});
  calculateMd5Sum(file, function(hash) {
    var data = {'md5sum': hash, 'size': file.size, 'model': 'image'};
    var settings = {
      'method': 'post',
      'dataType': 'json',
      'data': data,
      'success': function(result) {
        if (result.status == 'uploaded') {
          options['onUploadComplete'](result);
        } else if (result.status == 'uploading') {
          upload(file, result.upload_id, {
            onUploadComplete: function(result) {options['onUploadComplete'](result)},
            onChunkSent: function(offset) {options['onChunkSent'](offset)}
          });
        } else {
          alert('Unknown response');
        }
      }
    };
    $.ajax(options.getUploadURL, settings);
  })
};

var UploadView = Backbone.View.extend({
  tagName: 'div',
  className: 'image-list-row',
  template: _.template('<a href="#" class="remove">X</a><div class="thmbWrap"><img src="<%= thumbnail_url %>" class="thmb"><div class="indicator"></div></div><div class="filename"><%= filename %></div>'),
  inputTemplate: _.template('<input class="order" type="hidden" name="image_<%= image_pk %>_order" value="" />'),
  initialize: function() {
    $('#image-list').append(this.$el);
    this.render();
  },
  removeUploadFromDOM: function(cid) {
    var el = $("#" + cid);
    el.slideUp("slow", function() { el.remove(); updateOrders(); });
  },
  updateIndicator: function() {
    var v = (this.model.get('offset') / this.model.get('file').size) * 100;
    var indicatorEl = this.$el.find('.indicator');
    indicatorEl.animate({'width': v + '%'});
    if (Math.round(v) === 100) {
      indicatorEl.slideUp();
    }
  },
  updateThumbnailImage: function(thumbnail_url) {
    var imgEl = this.$el.find('img');
    imgEl.attr('src', thumbnail_url);
    imgEl.animate({opacity: 1});
  },
  render: function(){
    this.$el.html(this.template({
      'thumbnail_url': this.model.get('thumbnail_url'),
      'filename': trimFileName(this.model.get('file').name, 30),
    }));
    this.updateIndicator();
  }
});

var Upload = Backbone.Model.extend({
  initialize: function() {
    var _this = this;
    getUpload(this.get('file'), {
      onUploadComplete: function (result) {
        _this.set('offset', _this.get('file').size);
        _this.set('thumbnail_url', result.object.thumbnail_url);
        _this.view.updateThumbnailImage(result.object.thumbnail_url);
        _this.view.updateIndicator();
        _this.view.$el.append(_this.view.inputTemplate({'image_pk': result.object.pk}));
        updateOrders();
      }, 
      onChunkSent: function(offset) {
        _this.set('offset', offset);
        _this.view.updateIndicator();
      }
    });
  }
});

var UploadList = Backbone.Collection.extend({model: Upload});

var UploadListView = Backbone.View.extend({
  events: {'click #image-select-box' : 'openFileSelect',
           'change #id_images'       : 'addFiles',
           'click .remove'           : 'removeFile'},
  el: 'form',
  initialize: function(){
    _.bindAll(this, 'render', 'addFile');
    this.collection = new UploadList();
    this.collection.bind('add', this.appendUploadToDOM);
    this.counter = 0;
    this.render();
  },
  openFileSelect: function(){
    $('#id_images').trigger('click');
  },
  addFiles: function() {
    var files = document.getElementById('id_images').files;
    for (var i = 0; i < files.length; i++) {
      this.addFile(files[i]);
    }
  },
  removeFile: function(ev) {
    var cid = $(ev.currentTarget).parent()[0].getAttribute("id");
    var upload = this.collection.find({'cid': cid});
    upload.view.removeUploadFromDOM(cid);
    this.collection.remove(upload);
    return false;
  },
  addFile: function(file){
    this.counter++;
    var upload = new Upload({'file': file, 'order': this.counter});
    var uploadView = new UploadView({model: upload, id: upload.cid});
    upload.view = uploadView;
    this.collection.add(upload);
  },
});

var uploadListView = new UploadListView();
window.ulw = uploadListView;

$(function() {
  $('#image-list').sortable().bind('sortupdate', function() {
     updateOrders();
  });
})
