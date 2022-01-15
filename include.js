var protocol = 'ws';
if (window.location.protocol == 'https:') {
  protocol = 'wss'
}
var ws = new ReconnectingWebSocket(protocol + "://" + location.host + "/websocket");
var states = {
  1:0,
  2:0,
  3:0,
  4:0,
  5:0,
  6:0,
  7:0,
  8:0
};
var routines = {};

$(window).keydown(function (e) {
  switch(e.which) {
  case 49:
  press(1);
  break;
  case 50:
  press(2);
  break;
  case 51:
  press(3);
  break;
  case 52:
  press(4);
  break;
  case 53:
  press(5);
  break;
  case 54:
  press(6);
  break;
  case 55:
  press(7);
  break;
  case 56:
  press(8);
  break;
  }
});

function checkAllOnOff() {
  console.log(states);
  seton = 0;
  setoff = 0;
  for( let i in states) {
    console.log(states[i]);
    if (states[i] == 0) {
      setoff = setoff + 1;
    } else {
      seton = seton + 1;
    }
    if (seton > 0 && setoff > 0) {
      setHighlight("routine-Allon",0);
      setHighlight("routine-Alloff",0);
    }
  }
  if (seton == 8) {
    setHighlight("routine-Allon",1);
    setHighlight("routine-Alloff",0);
  }
  if (setoff == 8) {
    setHighlight("routine-Alloff",1);
    setHighlight("routine-Allon",0);
  }
}
function setHighlight(mydiv,onoff) {
  color="white";
  if (onoff == 1) {
    color="lightGrey";
  }
  $("#"+mydiv).css("background-color",color);
}

function press(id) {
  newstate = 0;
  if(states[id] == 0) {
    newstate = 1;
  }
  ws.send(JSON.stringify({"action": "setid", "id":id, "state": newstate}));
  checkAllOnOff();
}
function runRoutine(name) {
  console.log("runRoutine: "+name);
  if(name == "Allon" || name == "Alloff") {
    ws.send(JSON.stringify({"action": "stop"}));
  }

  ws.send(JSON.stringify({"action": "routine", "routine":name}));
  checkAllOnOff();
}
function handleRoutine(name,state) {
        divid = 'routine-'+name;
        //Add to list of routines or set the state either way
        routines[name]=state;
        //Add to page, if doesn't exist
        if($('#'+divid).length < 1) {
            containerdiv = '#routines-container';
            if(name == "Allon" || name == "Alloff") {
                containerdiv = '#onoff-container';
            }
            newcircle = "<div id='"+divid+"' class='smallcircle' onclick='runRoutine(\""+name+"\")'>"+name+"</div>";
            $(containerdiv).append(newcircle);
        }
		if (state ==1 ) {
			$("#"+divid).css('border-color', 'green');
            $("#"+divid).css('border-width','10px');
		} else {
			$("#"+divid).css('border-color', 'black');
            $("#"+divid).css('border-width','1px');
		}
}
ws.onmessage = function(evt) {
    var messageDict = JSON.parse(evt.data);
    action = messageDict.action;
    console.log(messageDict);
    // messageDict attributes are accessable like messageDict.user, messageDict.id, etc
    if( action == "state") {
        id = messageDict.id;
        state = messageDict.state;
        states[id] = state;
        if(state == "1") {
            $("#"+id).css('background-color','green');
            $("#div"+id).css('border-color', 'green');
        } else if (state == "0") {
            $("#"+id).css('background-color','red');
            $("#div"+id).css('border-color', 'red');
        }
        checkAllOnOff();
    } else if (action == "routine" ) {
        name = messageDict.name;
        state = messageDict.state;
        handleRoutine(name,state);
    } else if (action == "routineState") {
        name = messageDict.name;
        state = messageDict.state;
        divname = '#routine-'+name;
        color = 'black';
        if (state == 1) {
            color = 'green';
        }
        $(divname).css('border-color', color);
    }
};

