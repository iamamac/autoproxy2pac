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

/* PAC configure page */
function getPacUrl(){
    var name = $("input[name='name']:checked").val();
    if (name != "custom") 
        return name;
    var host = $("input[name='host']").val();
    var port = $("input[name='port']").val();
    if (host && port) 
        return $("select[name='type']").val().toLowerCase() + "/" + host + "/" + port;
    $.facebox("请填写代理信息或选择你使用的代理工具");
}
