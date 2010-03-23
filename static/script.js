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
