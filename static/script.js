/* Two-column template */
function loadChangelog(){
    $('div.feedburnerFeedBlock h3').each(function(){
        $(this).next('ul').children('li').each($(this).text() != '规则调整' ? function(){
            var item = $(this).html();
            $(this).html(item.slice(0, item.indexOf('(')));
        }
 : function(){
            var item = $(this).html();
            $(this).html(item.slice(item.indexOf('(') + 1, item.indexOf(')')));
        });
        $(this).remove();
    });
    $('div.feedburnerFeedBlock').replaceAll('#changelog p').fadeIn();
}
