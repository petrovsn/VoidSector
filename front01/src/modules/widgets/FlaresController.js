import React from 'react'
import { get_http_address } from '../network/connections'
import { timerscounter } from '../utils/updatetimers'
import { get_locales } from '../locales/locales'
import { get_solarflare } from '../network/connections'
import { send_command } from '../network/connections'

export class FlaresController extends React.Component {
    constructor() {
        super()
        this.state = {
            sf_timer_value: 0
        }
    }

    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.onUpdate, 1000)
        timerscounter.add(this.constructor.name, timer_id)
    }

    onUpdate = () => {
        this.forceUpdate()
    }

    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }


    get_solarFlare_control = () => {
        let sf_state = get_solarflare()
        if (!sf_state) return <div></div>
        return (
            <div className='solarFlare_control'>
                <label>
                    <b>Solar flare state:</b>{sf_state["state"].toString()}
                </label>
                <label>
                    time2nextphase:{sf_state["time2nextphase"]}
                </label>
                <label>
                    probability:{sf_state["probability"]}
                </label>
                <button onClick={() => { this.toogleSolarFlare(!sf_state["state"]) }}>TOOGLE ACTIVITY</button>
                <button onClick={() => { this.toogleSolarFlareTimer(!sf_state["timer_state"]) }}>TOOGLE TIMER</button>
                <input type='number' onChange={(e) => { this.setState({ "sf_timer_value": e.target.value }) }}></input>
                <button onClick={() => { this.setSolarFlareTimer() }}>SET TIMER OF CURRENT PHASE</button>
                <button onClick={() => { this.setHighProbFlare() }}>SET HIGH PROB</button>
                <button onClick={() => { this.setLowProbFlare() }}>SET LOW PROB</button>
            </div>
        )
    }

    setHighProbFlare = ()=>{
        send_command("solar_flare", "admin", "set_probability_value", { 'value': "high" })
    }

    setLowProbFlare = ()=>{
        send_command("solar_flare", "admin", "set_probability_value", { 'value': "low" })
    }

    toogleSolarFlare = (value) => {
        send_command("solar_flare", "admin", "set_solar_flare", { 'state': value })
    }

    toogleSolarFlareTimer = (value) => {
        send_command("solar_flare", "admin", "set_timer_state", { 'state': value })
    }

    setSolarFlareTimer = () => {
        send_command("solar_flare", "admin", "set_timer_value", { 'value': this.state.sf_timer_value })
    }

    render() {
        let result = this.get_solarFlare_control()
        return result
    }
}
