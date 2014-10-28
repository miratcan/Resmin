(function($){
  var Upload = Backbone.Model.extend();
  var UploadList = Backbone.Collection.extend({model: Upload});
  var UploadListView = Backbone.View.extend({

    events: {'click #image-select-box' : 'openFileSelect',
             'change #id_images'       : 'addFiles',
             'click .remove'           : 'removeFile'},

    el: 'form',
    template: _.template('<div class="image-list-row" id="<%= cid %>"><a href="#" class="remove">X</a><div class="thmbWrap"><img src="" class="thmb"><div class="indicator"></div></div><div class="filename"><%= filename %></div></div>'),

    initialize: function(){
      _.bindAll(this, 'render', 'addFile', 'appendUpload', 'removeFile');
      this.collection = new UploadList();
      this.collection.bind('add', this.appendUpload);
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

    removeFile: function(e) {
      var id = $(e.currentTarget).parent()[0].getAttribute("id");
      var upload = this.collection.find({'cid': id});
      var el = $("#" + id)
      this.collection.remove(upload);
      el.slideUp("slow", function() { el.remove(); });
      return false;
    },

    fileNameExt: function(filename) {
      var a = filename.split(".");
      if( a.length === 1 || ( a[0] === "" && a.length === 2 ) ) {
        return "";
      }
      return a.pop();  // feel free to tack .toLowerCase() here if you want
    },

    trimmedFileName: function(filename, ml, pl) {
      var ml = ml || 20;
      var pl = pl || 5;
      if (filename.length > ml) {
        var ext = this.fileNameExt(filename);
        var postfixLength = ext.length + pl
        var postfixStart = filename.length - postfixLength;
        var postfixEnd = filename.length;
        var prefixStart = 0;
        var prefixEnd = ml - (postfixLength + 3);
        return filename.slice(prefixStart, prefixEnd) + "..." + filename.slice(postfixStart, postfixEnd);
      } else {
        return filename;
      }
    },

    appendUpload: function(upload){
      var file = upload.get('imageFile')
      var row = this.template({
        'cid': upload.cid,
        'filename': this.trimmedFileName(file.name, 30),
      });
      this.$el.find("#image-list").append(row);
    },

    render: function(){
      var self = this;
      _(this.collection.models).each(function(upload){
        self.appendUpload(upload);
      }, this);
    },

    addFile: function(imageFile){
      this.counter++;
      var upload = new Upload({imageFile: imageFile, order: this.counter});
      this.collection.add(upload);
    },

  });

  var uploadListView = new UploadListView();
  window.ulw = uploadListView;

  $('#id_images').fileupload({
    dataType: 'json',
    url: '/up/',
    maxChunkSize: 1024 * 100,
    sequentialUploads: true,
    add: function (e, data) {
      console.log(data);
      uploadListView.addFile(data.files[0]);
      data.submit();
    },
    done: function (e, data) {
      console.log('uploaded: ' + data);
    }
  });
})(jQuery)

$(document).ready(function() {
  $( "#image-list" ).sortable();

});

