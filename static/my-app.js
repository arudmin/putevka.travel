// Initialize your app
var myApp = new Framework7();

// Export selectors engine
var $$ = Dom7;

// Add view
var mainView = myApp.addView('.view-main', {
    // Because we use fixed-through navbar we can enable dynamic navbar
    dynamicNavbar: true
});

myApp.onPageReinit('index', function (page) {
    // run createContentPage func after link was clicked
    $$('.close-item-link').on('click', function () {
        myApp.closePanel();
    });
    var a=document.getElementsByTagName("a");
    for(var i=0;i<a.length;i++) {
        if(!a[i].onclick && a[i].getAttribute("target") != "_blank") {
            a[i].onclick=function() {
                    window.location=this.getAttribute("href");
                    return false; 
            }
        }
    }
});

var device = Framework7.prototype.device;
if (device.iphone) {
  addToHomescreen();
}

