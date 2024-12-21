
import React from 'react'
import { send_command, get_navdata, get_http_address } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';

export class HBodiesSelector extends React.Component {
    constructor(props) {
        super(props);


        this.state = {
            hbodies_data: {},
            lbodies_data: {},
            slots_in_row: 7,

        }
    }
    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.proceed_data_message, 30)
        timerscounter.add(this.constructor.name, timer_id)
    }

    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }

    proceed_data_message = () => {
        let nav_data = get_navdata()
        if (!nav_data) return
        let hbodies_data = {}
        let lbodies_data = {}

        for (let k in nav_data["hBodies"]) {
            hbodies_data[k] = nav_data["hBodies"][k]
        }

        for (let k in nav_data["lBodies"]) {
            lbodies_data[k] = nav_data["lBodies"][k]
        }
        this.setState({
            "hbodies_data": hbodies_data,
            "lbodies_data": lbodies_data
        })



    }

    take_control = (key) => {
        send_command("map_editor", "admin", "select_body", { 'mark_id': key })
        this.props.onBodySelect(key)
    }
    delete = (key) => {
        send_command("map_editor", "admin", "delete_body", { 'mark_id': key })
        this.props.onBodySelect(key)
    }

    release_control = (key)=>{
        send_command("map_editor", "admin", "select_body", { 'mark_id': null })
        this.props.onBodySelect(key)
    }

    copy_entity = (key) => {
        send_command("map_editor", "admin", "copy_body", { 'mark_id': key })
        this.props.onBodySelect(key)
    }


    get_control_widget = (key, data) => {
        return (
            <div
                className='bodySelectorWidget'
                onMouseEnter={(e) => { this.props.onBodyHighlight(key) }}
                onMouseLeave={(e) => { this.props.onBodyHighlight(null) }}
            >
                <label>{data["type"]}</label>
                <label>{key}</label>


                <button onClick={(e) => { this.take_control(key) }}> select </button>
                <button onClick={(e) => { this.release_control(key) }}> release </button>
                <button onClick={(e) => { this.copy_entity(key) }}> copy </button>
                <button onClick={(e) => { this.delete(key) }}> delete </button>
            </div>

        )
    }




    get_hbodies_list = () => {
        let percs = 100 / this.state.slots_in_row;
        let style_grid = ""
        for (let i = 0; i < this.state.slots_in_row; i++) {
            style_grid = style_grid + percs.toFixed(2).toString() + "% "
        }
        let hbodies = []
        for (let k in this.state.hbodies_data) {
            if (this.state.hbodies_data[k]) {
                hbodies.push(
                    this.get_control_widget(k, this.state.hbodies_data[k])
                )
            }
        }
        return <div className='BodiesSelector_section'
            style={{
                "grid-template-columns": style_grid
            }}
        >{hbodies}</div>
    }

    get_lbodies_list = () => {
        let lbodies = []
        let percs = 100 / this.state.slots_in_row;
        let style_grid = ""
        for (let i = 0; i < this.state.slots_in_row; i++) {
            style_grid = style_grid + percs.toFixed(2).toString() + "% "
        }

        for (let k in this.state.lbodies_data) {

            if (this.state.lbodies_data[k]) {
                if (!["Mine_type2", "MeteorsCloud"].includes(this.state.lbodies_data[k].type)){
                    lbodies.push(
                        this.get_control_widget(k, this.state.lbodies_data[k])
                    )
                }
                
            }
        }
        return <div className='BodiesSelector_section'
            style={{
                "grid-template-columns": style_grid
            }}>{lbodies}</div>
    }

    render() {

        return (<div className='BodiesSelector div_vertical'>
            <b>"BodiesSelector"</b>
            <input type="number" onChange={(e) => { this.setState({ "slots_in_row": e.target.value }) }} value={this.state.slots_in_row}></input>
            {this.get_hbodies_list()}

            {this.get_lbodies_list()}
        </div>)

    }
}



export class BodyEditor extends React.Component {
    constructor(props) {
        super(props);


        this.state = {
            selected_body_idx: null,
            selected_body_ref: {},
            selected_body_edit: {},
            selected_body_stats: {},
            forced: false
        }
    }

    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.proceed_data_message, 30)
        timerscounter.add(this.constructor.name, timer_id)
    }

    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }

    compare_selection_heavy = (body) => {
        for (let k in body) {
            if (k in this.state.selected_body_ref) {
                if (this.state.selected_body_ref[k] !== body[k]) {
                    return false
                }
            }
            else {
                return false
            }
        }
    }

    //#region SELECTION UPDATE
    compare_selection = (body) => {
        let tmp1 = Object.assign({}, this.state.selected_body_ref)
        let tmp2 = Object.assign({}, body)
        delete tmp1["pos"]
        delete tmp1["vel"]
        delete tmp2["pos"]
        delete tmp2["vel"]
        return JSON.stringify(tmp1) === JSON.stringify(tmp2)
    }

    find_in_navdata = (mark_id, navdata) => {
        let tmp = null
        if (mark_id in navdata["lBodies"]) {
            tmp = navdata["lBodies"][mark_id]
        }
        else if (mark_id in navdata["hBodies"]) {
            tmp = navdata["hBodies"][mark_id]
        }
        return tmp
    }

    proceed_data_message = () => {
        let nav_data = get_navdata()
        if (!nav_data) return
        if (this.props.selected_body_idx) {
            let selected_body = this.find_in_navdata(this.props.selected_body_idx, nav_data)
            if (!this.compare_selection(selected_body)) {



                this.setState({
                    selected_body_edit: Object.assign({}, selected_body),
                    selected_body_ref: Object.assign({}, selected_body),
                    selected_body_idx: this.props.selected_body_idx
                }, this.update_body_stats)
            }
        }
    }
    //#endregion


    //#region ATTRIBUTES

    change_attribute = (key, value) => {
        let tmp_num = parseFloat(value)
        if (isNaN(tmp_num)) tmp_num = value

        let edited_body_tmp = this.state.selected_body_edit
        edited_body_tmp[key] = tmp_num
        this.setState({ selected_body_edit: edited_body_tmp }, this.update_body_stats)
    }


    get_attributes = () => {
        let result = []
        for (let k in this.state.selected_body_edit) {
            if (!(["predictions", "vel"].includes(k))) result.push(<label>{k}: <input onChange={(e) => { this.change_attribute(k, e.target.value) }} value={this.state.selected_body_edit[k]}></input></label>)

        }
        let k = "forced"
        result.push(<label>{k}: <input type="checkbox" onChange={(e) => {
            this.setState({ forced: e.target.value })
            //console.log("e.target.value", e.target)
        }} value={this.state.forced}></input></label>)
        return result
    }

    commit_attribute = () => {
        send_command("map_editor", "admin", "change_body", { "descr": this.state.selected_body_edit, "forced": this.state.forced })
        this.setState({
            selected_body_idx: null
        })
    }

    //#endregion


    update_body_stats = () => {
        if (this.state.selected_body_edit.length === 0) return;
        if (!("gr" in this.state.selected_body_edit)) return;
        let header_content = {
            "Content-Type": "application/json",
            "Body-Description": JSON.stringify(this.state.selected_body_edit)
        }

        var myInit = {
            method: "GET",
            headers: header_content,
        }

        return fetch(get_http_address() + "/utils/orbital_stats", myInit)
            .then(response => {
                let code = response.status;

                switch (code) {
                    case 200:
                        let data = response.json()
                        return data
                    default:
                        break;
                }
            })
            .then(data => {

                this.setState({
                    selected_body_stats: data
                })
            })
    }

    get_body_stats = () => {
        let result = []
        for (let field in this.state.selected_body_stats) {
            result.push(
                <label>
                    {field}: {this.state.selected_body_stats[field]}
                </label>
            )
        }
        return result

    }


    render() {
        return (
            <div className='BodyEditor'>
                <div
                    className='div_vertical'>
                    <b>BodyEditor</b>
                    {this.get_attributes()}
                    <button onClick={(e) => { this.commit_attribute() }}>Commit</button>
                </div>
                <div
                    className='div_vertical'>
                    <b>BodyStats</b>
                    {this.get_body_stats()}
                </div>

            </div>)
    }
}





export class BodySpawner extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            spawned_entity_type: "",
            spawned_entity_markId: "",
        }
    }



    commit_spawn = () => {
        send_command("map_editor", "admin", "spawn_body", {
            "entity_type": this.state.spawned_entity_type,
            "mark_id": this.state.spawned_entity_markId,
        })
        this.setState({
            spawned_entity_markId: ""
        })
    }

    get_entitytype_selector = () => {
        let options = [<option key={""} value={""}> {""} </option>]
        let options_list = ["ae_Ship", "NPC_Ship", "NPC_Kraken", "SpaceStation", "SpaceStationDebris", "hBody", "ResourceAsteroid", "Mine_type1", "Mine_type2", "WormHole", "MeteorsCloud", "QuantumShadow", "pjtl_Mine", "ShipDebris", "intact_Container"]
        for (let i in options_list) {
            let option = options_list[i]
            options.push(<option key={option} value={option}> {option} </option>)
        }
        return <select onChange={(e) => { this.setState({ "spawned_entity_type": e.target.value }) }}>{options}</select>
    }

    render() {
        return (<div
            className='div_vertical'>
            <b>BodySpawner</b>
            {this.get_entitytype_selector()}
            <label>MarkID: <input onChange={(e) => { this.setState({ "spawned_entity_markId": e.target.value }) }} value={this.state.spawned_entity_markId}></input></label>
            <button onClick={(e) => { this.commit_spawn() }}>SPAWN</button>
        </div>)
    }
}






export class MapLoader extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            map_list: [],
            map_name: ""
        }
    }


    componentDidMount() {
        let timer_id = timerscounter.get("MapLoader")

        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.updateContent, 1000)
        timerscounter.add("MapLoader", timer_id)
        this.updateContent()
    }


    componentWillUnmount() {
        let timer_id = timerscounter.get("MapLoader")
        clearInterval(timer_id)
    }


    updateContent = () => {
        var myInit = {
            method: "GET",
            headers: {
            },
        }

        return fetch(get_http_address() + "/admin/maps", myInit)
            .then(response => {
                let code = response.status;

                switch (code) {
                    case 200:
                        let data = response.json()
                        return data
                    default:
                        break;
                }
            })
            .then(data => {

                this.setState({
                    map_list: data
                })
            })
            .catch(error => {

            });
    }

    get_map_list = () => {
        let result = []
        for (let i in this.state.map_list) {
            let map = this.state.map_list[i]
            result.push(
                <label onClick={() => { this.onLoadSelected(map) }} >{map}</label>
            )
        }
        return <div className='map_selector'>{result} </div>
    }

    onSaveCurrent = () => {
        send_command("map_editor", "admin", "save_map", { "map_name": this.state.map_name })
    }

    onLoadSelected = (map_name) => {
        this.setState({ "map_name": map_name.split('.')[0] })
        send_command("map_loader", "admin", "load_map", { "map_name": map_name })
    }

    render() {
        return (<div
            className='FileLoader'
        >
            <b>MapLoader</b>
            {this.get_map_list()}

            <input onChange={(e) => { this.setState({ "map_name": e.target.value }) }} value={this.state.map_name}></input>
            <button onClick={this.onSaveCurrent}>SAVE</button>
        </div>)
    }
}


export class ShipScreenLoader extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            map_list: [],
            map_name: ""
        }
    }


    componentDidMount() {
        let timer_id = timerscounter.get("ShipScreenLoader")

        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.updateContent, 1000)
        timerscounter.add("ShipScreenLoader", timer_id)
        this.updateContent()
    }


    componentWillUnmount() {
        let timer_id = timerscounter.get("ShipScreenLoader")
        clearInterval(timer_id)
    }


    updateContent = () => {
        var myInit = {
            method: "GET",
            headers: {
            },
        }

        return fetch(get_http_address() + "/admin/ship_screens", myInit)
            .then(response => {
                let code = response.status;

                switch (code) {
                    case 200:
                        let data = response.json()
                        return data
                    default:
                        break;
                }
            })
            .then(data => {

                this.setState({
                    map_list: data
                })
            })
            .catch(error => {

            });
    }

    get_map_list = () => {
        let result = []
        for (let i in this.state.map_list) {
            let map = this.state.map_list[i]
            result.push(
                <label onClick={() => { this.onLoadSelected(map) }} >{map}</label>
            )
        }
        return <div className='map_selector'>{result} </div>
    }

    onSaveCurrent = () => {
        send_command("map_editor", "admin", "save_main_ship", { "screen_name": this.state.map_name })
    }

    onLoadSelected = (map_name) => {
        this.setState({ "map_name": map_name.split('.')[0] })
        send_command("map_loader", "admin", "load_main_ship", { "screen_name": map_name })
    }

    render() {
        return (<div
            className='FileLoader'
        >
            <b>ShipScreens</b>
            {this.get_map_list()}

            <input onChange={(e) => { this.setState({ "map_name": e.target.value }) }} value={this.state.map_name}></input>
            <button onClick={this.onSaveCurrent}>SAVE</button>
        </div>)
    }
}
