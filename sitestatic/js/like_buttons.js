$(document).ready(function() {
  $(".like-button").click(function(ev) {
    var target = $(ev.target).parent();
    $.ajax({
      type: "POST",
      url: "/l/",
      data: {
        "aid" : target.attr('data-answer-id'),
        "v"   : target.find(".heart").hasClass("pink") ? 0 : 1
      },
      dataType: "json",
      success: function(data) {
        target.find(".count").html(data['like_count']);
        if (data['status']===true) {
          target.find(".heart").toggleClass("pink");
        }
      }
    });
  });
});
