$('body').on('click', '.apavolku-galocksed', function(){
    if ($(this).is(':checked')){
    $('#passw1').attr('type', 'text');
    $('#passw2').attr('type', 'text');
    } else {
    $('#passw1').attr('type', 'password');
    $('#passw2').attr('type', 'password');
    }
  });