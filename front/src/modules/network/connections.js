

import { ip } from "../configs/configs";

let path2server_ws = "ws://" + ip + ":5000/"
let path2server_http = "http://" + ip + ":1924/"


let websocket = new WebSocket(path2server_ws);
let input_message_string = ""
let input_message_last_timestamp = ""
let input_message_last_json = {}

export function addEventListener(f) {
    if (websocket) websocket.addEventListener("message", f)
}
export function removeEventListener(f) {
    if (websocket) websocket.removeEventListener("message", f)
}


function parse_message_to_json(){
    try{
        input_message_last_json = {}
        let tmp_json = JSON.parse(input_message_string)
        if (tmp_json) input_message_last_json = tmp_json
    }
    catch(error){
        console.log("parse_message_to_json",error)
        input_message_last_json = {}
    } 
    
}

function receive_message({ data }) {
    input_message_string = data
    input_message_last_timestamp = new Date()
    parse_message_to_json()
}

websocket.addEventListener("message", receive_message)


function check_connection_and_update() {
    //console.log("check_connection_and_update", websocket)
    send_command("connection", "admin", "ping", {})
    if (new Date() - input_message_last_timestamp > 300) {
        websocket.removeEventListener("message", receive_message)
        try {
            websocket = new WebSocket(path2server_ws);
            websocket.addEventListener("message", receive_message)
        }
        catch (error) {

        }




    }
}

//setInterval(check_connection_and_update, 1000)

export function get_websocket() {
    return websocket
}


export function get_http_address() {
    return path2server_http
}

export let current_mark_id = null

export function send_command(level, target_id, command, params, null_confirmed = false) {
    if (websocket.readyState !== 1) return
    if (!null_confirmed) if (!target_id) if (command !== "take_control_on_entity") return
    if (command === "take_control_on_entity") current_mark_id = target_id



    let res = {
        "level": level,
        "target_id": target_id,
        "action": command,
        "params": params
    }

    websocket.send(JSON.stringify(res));
}



export function get_system_state(system_name) {
    let message_data_json = input_message_last_json
    if (typeof (message_data_json) != typeof ({})) return null
    if (!("state_data" in message_data_json)) return null
    if (!message_data_json['state_data']) return null
    if (!(system_name in message_data_json['state_data'])) return null
    return message_data_json['state_data'][system_name]
}


export function get_navdata() {
    try {
        let message_data_json = input_message_last_json
        if (typeof (message_data_json) != typeof ({})) return null
        if (!("nav_data" in message_data_json)) return null
        if (!("hBodies" in message_data_json['nav_data'])) return null
        if (!("lBodies" in message_data_json['nav_data'])) return null
        return message_data_json['nav_data']
    } catch (error) {
        return null
    }



}


export function get_performance() {
    let message_data_json = input_message_last_json
    if (typeof (message_data_json) != typeof ({})) return null
    if (!("performance" in message_data_json)) return null
    return message_data_json['performance']
}


export function get_server_systems_state() {
    let message_data_json = input_message_last_json
    if (typeof (message_data_json) != typeof ({})) return null
    if (!("systems_state" in message_data_json)) return null



    return message_data_json['systems_state']
}


export function get_ships_state() {
    let message_data_json = input_message_last_json
    if (typeof (message_data_json) != typeof ({})) return null
    if (!("ships_state" in message_data_json)) return null
    return message_data_json['ships_state']
}



export function get_stations_state() {
    let message_data_json = input_message_last_json
    if (typeof (message_data_json) != typeof ({})) return null
    if (!("stations_state" in message_data_json)) return null
    return message_data_json['stations_state']
}

export function get_observer_id() {
    let message_data_json = input_message_last_json
    if (typeof (message_data_json) != typeof ({})) return null
    if (!("observer_id" in message_data_json)) return null
    return message_data_json['observer_id']



}

export function get_capmarks() {
    let message_data_json = input_message_last_json
    if (typeof (message_data_json) != typeof ({})) return null
    if (!("cap_marks" in message_data_json)) return null
    return message_data_json['cap_marks']
}

export function get_solarflare() {
    let message_data_json = input_message_last_json
    if (typeof (message_data_json) != typeof ({})) return null
    if (!("solar_flare" in message_data_json)) return null
    return message_data_json['solar_flare']
}


export function get_medicine_state(username) {
    let message_data_json = get_system_state("med_sm")
    if (!message_data_json) return true
    if (!("roles" in message_data_json)) return true
    return !message_data_json["roles"][username]["disabled"]

}

export function take_control(key) {
    send_command("connection", key, "take_control_on_entity", { 'target_id': key })
}


export function is_taking_damage() {
    let message_data_json = get_system_state("damage_sm")
    if (!message_data_json) return false
    return message_data_json["is_taking_damage"]
}



export function get_map_border() {
    let message_data_json = input_message_last_json
    if (typeof (message_data_json) != typeof ({})) return null
    if (!("map_border" in message_data_json)) return null
    return message_data_json['map_border']
}
