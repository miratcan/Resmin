/*
  TODO:
    * Check namings with javascript naming conventions.
    * Check for callback order.
    * Needs code review.
*/

/* Helper Functions ------------------------------------------------------- */

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
    return cookieValue
}

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
  var options = _.extend({chunkSize: 1024 * 100}, options || {});

  function readerOnLoad(ev) {
    spark.append(ev.target.result);
    if (offset >= file.size) {
      func(spark.end());
    } else {
      offset += options.chunkSize;
      loadChunk();      
    }
  }

  function readerOnError() {
    console.warn('something went wrong');
  }

  function loadChunk() {
    var fileReader = new FileReader();
    var start = offset;
    var end = ((start + options.chunkSize) >= file.size) ? file.size : start + options.chunkSize;
    fileReader.onload = readerOnLoad.bind(this);
    fileReader.onerror = readerOnError.bind(this);
    fileReader.readAsArrayBuffer(sliceMethod.call(file, start, end));

  }

  loadChunk();
}

function fileNameExt(filename) {
  var a = filename.split(".");
  if( a.length === 1 || ( a[0] === "" && a.length === 2 ) ) {
    return "";
  }
  return a.pop().toLowerCase();
}

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
}

function upload(file, upload_id, options) {
    var options = _.extend({
      chunkSize: 1024 * 100,
      urlPrefix: '/upload/',
      onUploadComplete: function(result) {},
      onChunkSent: function(offset) {}
    }, options || {});
    var fileSize = file.size;
    var uploadRequest = new XMLHttpRequest();

    function _contentRangeHeaderText(rangeStart, rangeEnd) {
        return 'bytes ' + rangeStart + '-' + rangeEnd + '/' + fileSize
    }

    function _upload(rangeStart, rangeEnd) {
      if (rangeEnd > fileSize) { rangeEnd = fileSize; };
      var chunk = file.slice(rangeStart, rangeEnd);
      uploadRequest.open('PUT', options['urlPrefix'] + upload_id + '/', true);
      uploadRequest.overrideMimeType('application/octet-stream');
      uploadRequest.setRequestHeader('Content-Range', _contentRangeHeaderText(rangeStart, rangeEnd));
      uploadRequest.setRequestHeader("X-CSRFToken", csrftoken)
      uploadRequest.send(chunk);
    }

    uploadRequest.onreadystatechange = function() {
      if (uploadRequest.readyState == 4 && uploadRequest.status == 200) {
        var result = JSON.parse(uploadRequest.responseText);
        if (result.status == 'uploaded') {
          options['onUploadComplete'](result);
        } else {
          options['onChunkSent'](result.offset);
          var rangeStart = result.offset;
          var rangeEnd = Math.min(fileSize, rangeStart + options['chunkSize'])
          _upload(rangeStart, rangeEnd);
        }
      }
    };
    _upload(0, Math.min(options['chunkSize'], fileSize));
};

function getFile(file, options) {

  var options = _.extend({
    uploadURL: '/upload/',
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
            onUploadComplete: function(result) { options['onUploadComplete'](result) },
            onChunkSent: function(offset) { options['onChunkSent'](offset) }
          });
        } else {
          alert('Unknown response');
        }
      }
    };

    $.ajax(options.uploadURL, settings);

  })
};

function updateSorted() {
  $('#slot-list').sortable('reload');
}

/* Backbone --------------------------------------------------------------- */

var SlotView = Backbone.View.extend({
  tagName: 'div',
  className: 'slot',
  attributes: {'draggable': true},
  template: _.template('<div class="thmbWrap"><img src="<%= thumbnailUrl %>" class="thmb" style="opacity: <%= opacity %>"><div class="indicator" style="width: <%= indicatorPercent %>"></div><a href="#" cid="<%= cid %>" class="remove">X</a></div>'),

  initialize: function() {
    this.id = "s" + this.model.cid;
    $('#slot-list').append(this.$el);
    this.render();
  },

  calculateOffsetPercent: function() {
    if (!this.model.get('fileCompleted')) {
      return Math.round(this.model.get('fileOffset') / this.model.get('fileSize') * 100);
    } else {
      return 100
    }
  },

  updateIndicator: function() {
    var indicatorEl = this.$el.find('.indicator');
    var percent = this.calculateOffsetPercent();
    indicatorEl.animate({'width': percent + '%'});
    if ((percent) === 100) {
      indicatorEl.slideUp();
    }
  },

  removeSlotFromDOM: function() {
    this.$el.remove();
    updateSorted();
  },

  render: function(){
    this.$el.html(this.template({
      'thumbnailUrl': this.model.get('thumbnailUrl') || '',
      'filename': this.model.get('filename') || '',
      'cPk': this.model.get('cPk') || '',
      'cTp': this.model.get('cTp') || '',
      'indicatorPercent': this.calculateOffsetPercent() || 0,
      'order': this.model.get('order'),
      'cid': this.model.cid,
      'opacity': this.model.get('fileCompleted') ? 1 : 0
    }));
  }

});

var Slot = Backbone.Model.extend({

  defaults: {
    cTp: 'image',
    fileCompleted: false
  },

  initialize: function() {
    var _this = this;
    var file = this.get('file');
    if (file !== undefined) {
      getFile(file, {
        onUploadComplete: function (result) {
          _this.set({
            'fileName': trimFileName(file.name, 30),
            'cPk': result.object.pk,
            'thumbnailUrl': result.object.thumbnail_url,
            'fileCompleted': true
          });
          _this.view.render();
        }, 
        onChunkSent: function(offset) {
          _this.set({'fileOffset': offset});
          _this.view.updateIndicator();
        }
      });
    };
    this.view = new SlotView({model: this});
  }

});

var SlotList = Backbone.Collection.extend({
  model: Slot });

var SlotListView = Backbone.View.extend({
  events: {'click #image-select-box' : 'openFileSelect',
           'change #id_images'       : 'addFiles',
           'click .remove'           : 'removeFile'},
  el: 'form',
  initialize: function(){
    _.bindAll(this, 'render', 'addFile');
    this.collection = new SlotList();
    this.collection.bind('add', this.appendSlotToDOM);
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
    $('#id_images').val('');
  },
  removeFile: function(ev) {
    var cid = $(ev.currentTarget)[0].getAttribute("cid");
    var slot = this.collection.find({'cid': cid});
    slot.view.removeSlotFromDOM(cid);
    this.collection.remove(slot);
    return false;
  },
  addFile: function(file){
    var list_of_orders = $('.order').map(function(idx, el) {
      return el.value
    });
    if (list_of_orders.length == 0) {
      list_of_orders = [0]
    };
    var order = Math.max.apply(null, list_of_orders) + 1;
    var upload = new Slot({file: file, order: order, fileOffset: 0,
                           fileSize: file.size, fileCompleted: false});
    this.collection.add(upload);
  },
  render: function() {
    var slotListEl = this.$el.find('slot-list');
    slotListEl.empty();
    _.each(this.collection.models, function(model) {
      slotListEl.append(model.view.render());
    });
  }
});
var uploadListView = new SlotListView();
uploadListView.collection.reset(slotData);
window.ulw = uploadListView;
$('#answer_form').submit(function() {
  $('.slot').each(function(idx, slotEl) {
    var cid = $(slotEl).find('.remove')[0].getAttribute('cid');
    var model = uploadListView.collection.find(function(item){
      return item.cid === cid;
    });
    model.set('order', idx + 1);
  });
  $('#id_slot_data').val(JSON.stringify(uploadListView.collection.toJSON()));
});