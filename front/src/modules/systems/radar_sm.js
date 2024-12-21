
import React from 'react'
import { send_command, get_system_state, get_observer_id } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';
import { NumericControlWidjet, NumericStepControlWidjet } from '../widgets/NumericControlWidget';
import '../../styles/RadarControlWidget.css'
import { get_locales } from '../locales/locales';
export class RadarControlWidget extends React.Component {
    on_set_radar_arc = (value) => {
        send_command("ship.radar_sm", get_observer_id(), "set_radar_arc", { "radar_arc": value })
    }

    on_set_radar_dir = (value) => {
        send_command("ship.radar_sm", get_observer_id(), "set_radar_dir", { "radar_dir": -value + 90 })
    }


    render() {
        return (
            <div
                className='SystemControlWidget'>
                <b>{get_locales("Radar control")}</b>
                <NumericStepControlWidjet

                    label={"distant_arc"}
                    init_value={10}
                    min={5}
                    max={360}
                    step={1}
                    onChange={this.on_set_radar_arc}
                />
                <NumericStepControlWidjet
                    label={"distant_dir"}
                    init_value={0}
                    min={-360}
                    max={+360}
                    step={3}
                    onChange={this.on_set_radar_dir}
                />
            </div>
        )
    }

}


export class RadarStatsWidget extends React.Component {
    constructor(props) {
        super(props);


        this.state = {
            data: {
            },
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
        let data = get_system_state("radar_sm")
        if (data) this.setState({ "data": data })
    }

    render() {
        return (
            <div className='RadarStatsWidget'>
                <label>{get_locales("close_range")}: {this.state.data.close_range}</label>
                <label>{get_locales("distant_range")}: {this.state.data.distant_range}</label>
                <label>{get_locales("distant_dir")}: {this.state.data.distant_dir}</label>
                <label>{get_locales("distant_arc")}: {this.state.data.distant_arc}</label>
            </div>)
    }
}
