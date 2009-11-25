function loadChangelog(element, name, num, start){
    if (!element || !name) 
        return;
    
    var url = "/changelog/" + name + ".json";
    if (num) {
        url += "?num=" + num;
        if (start) 
            url += "&start=" + start;
    }
    var req = new XMLHttpRequest();
    req.open("GET", url, false);
    req.send(null);
    logs = eval(req.responseText);
    
    element.innerHTML = "";
    for (var i in logs) {
        var log = logs[i];
        var entry = document.createElement("div");
        entry.className = "entry";
        
        var time = document.createElement("div");
        time.className = "time";
        time.innerHTML = log.time;
        entry.appendChild(time);
        
        for (var j in log.remove) {
            var item = document.createElement("div");
            item.className = "item-remove";
            var bullet = document.createElement("div");
            bullet.className = "bullet";
            var content = document.createElement("div");
            content.className = "content";
            content.innerHTML = log.remove[j];
            item.appendChild(bullet);
            item.appendChild(content);
            entry.appendChild(item);
        }
        for (var j in log.add) {
            var item = document.createElement("div");
            item.className = "item-add";
            var bullet = document.createElement("div");
            bullet.className = "bullet";
            var content = document.createElement("div");
            content.className = "content";
            content.innerHTML = log.add[j];
            item.appendChild(bullet);
            item.appendChild(content);
            entry.appendChild(item);
        }
        
        element.appendChild(entry);
    }
}
