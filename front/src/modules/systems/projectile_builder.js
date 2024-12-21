
import React from 'react'
import { send_command, get_http_address, current_mark_id } from '../network/connections';
import { get_locales } from '../locales/locales';
import { timerscounter } from '../utils/updatetimers';

export class ProjectileBuilderWidget extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            "mark_id": null,
            "details_list": ["thruster", "timer", "inhibitor", "explosive", "emp", "entities_detection", "projectiles_detection", "buster", "detonator", "decoy"],
            "stats_list": ["speed_up", "activation_time", "ttl_time", "explosion_radius/damage", "emp_radius", "ship_detection_radius", "projectiles_detection_radius", "velocity_penalty", "cost"],
            "blueprints": {

            },
            "edited_blueprint": {
                "thruster": 0,
                "timer": 0,
                "inhibitor": 0,
                "explosive": 0,
                "emp": 0,
                "entities_detection": 0,
                "projectiles_detection": 0,
                "buster": 0,
                "detonator": 0,
                "decoy": 0,
            },
            "stats": {
                "activation_time": 0,
                "cost": 0,
                "emp_radius": 0,
                "explosion_radius/damage": 0,
                "projectiles_detection_radius": 0,
                "ship_detection_radius": 0,
                "speed_up": 1,
                "ttl_time": 0,
                "details": 0,
                "velocity_penalty": 1
            },
            "selected": "new_blueprint_name"
        }
    }


    update_blueprints = () =>{
        var myInit = {
            method: "GET",
            headers: {
            },
            'cache-control':'no-store'
        }


        return fetch(get_http_address() + "projectile_constructor/" + current_mark_id + "/blueprints", myInit)
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
                    blueprints: data
                })
            })
            .catch(error => {

            });
    }

    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.update_blueprints, 1000)
        timerscounter.add(this.constructor.name, timer_id)
    }

    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }

    onComponentChange = (comp_name, step) => {
        let value = this.state.edited_blueprint[comp_name] + step
        if (value < 0) return
        let tmp_bp = this.state.edited_blueprint
        tmp_bp[comp_name] = value
        this.setState({ "edited_blueprint": tmp_bp }, this.updateStats)
    }

    updateStats = () => {
        var myInit = {
            method: "GET",
            headers: {
                "blueprint": JSON.stringify(this.state.edited_blueprint)
            },
            'cache-control':'no-store'
        }

        return fetch(get_http_address() + "/projectile_constructor/stats", myInit)
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
                    stats: data
                })
            })
            .catch(error => {

            });
    }

    get_components_selector = () => {
        let result = []
        for (let i in this.state.details_list) {
            let comp_name = this.state.details_list[i]
            result.push(
                <div className='component_controller'>
                    <label>{get_locales(comp_name)}</label>
                    <button onClick={(e) => { this.onComponentChange(comp_name, -1) }}> - </button>
                    <label>{this.state.edited_blueprint[comp_name]}</label>
                    <button onClick={(e) => { this.onComponentChange(comp_name, +1) }}> + </button>
                </div>
            )
        }
        return <div className="components_selector">{result}</div>
    }

    get_stats_panel = () => {
        let result = []
        for (let i in this.state.stats_list) {
            let stat_name = this.state.stats_list[i]
            result.push(
                <div className='component_controller'>
                    <label>{get_locales(stat_name)}:{this.state.stats[stat_name]}</label>
                </div>
            )
        }
        return <div className="components_selector">{result}</div>
    }

    onLoadSelected = (bp_name) => {
        let tmp_bp = Object.assign({},this.state.blueprints[bp_name])
        this.setState({
            "selected": bp_name,
            "edited_blueprint": tmp_bp
        }, this.updateStats)
    }

    onSaveCurrent = () => {
        send_command("ship.resources_sm", current_mark_id, "save_projectile_blueprint", {
            "bp_name": this.state.selected,
            "bp_content": this.state.edited_blueprint
        })
        let tmp_bps = this.state.blueprints
        tmp_bps[this.state.selected] = this.state.edited_blueprint
        this.setState({ "blueprints": tmp_bps })
    }

    onDeleteCurrent = () => {
        send_command("ship.resources_sm", current_mark_id, "delete_projectile_blueprint", {
            "bp_name": this.state.selected,
        })
        let tmp_bps = this.state.blueprints
        delete tmp_bps[this.state.selected]
        this.setState({ "blueprints": tmp_bps })
    }

    get_saveload_panel = () => {
        let blueprints = []
        for (let bp_name in this.state.blueprints) {
            blueprints.push(
                <label className={this.state.selected === bp_name ? "selected" : ""} onClick={() => { this.onLoadSelected(bp_name) }} >{bp_name}</label>
            )
        }
        return <div
            className='FileLoader'
        >
            <div className='map_selector'>{blueprints} </div>
            <input onChange={(e) => {
                if (e.target.value.length < 20) {
                    this.setState({ "selected": e.target.value })
                }
            }} value={this.state.selected}></input>
            <button onClick={this.onSaveCurrent}>{get_locales("SAVE")}</button>
            <button onClick={this.onDeleteCurrent}>{get_locales("DELETE")}</button>
        </div>

    }

    render() {
        return (
            <div className='SystemControlWidget'>
                <label><b>{get_locales("Projectile constructor")}</b></label>
                <div className='ProjectileBuilderWidget'>
                    {this.get_saveload_panel()}
                    <div className="DesignSection">
                        {this.get_components_selector()}
                        {this.get_stats_panel()}
                    </div>
                </div>
            </div>
        )
    }

}
