
import React from 'react'


import { PlayersRadarWidget } from './modules/widgets/PlayerRadar.js';
import './styles/PilotStation.css'
import { get_observer_id, get_system_state } from './modules/network/connections.js';
import { timerscounter } from './modules/utils/updatetimers.js';

import { take_control } from './modules/network/connections.js';
export class CommonRadarStation extends React.Component {
    constructor(props) {
        super(props);


        this.state = {
            selected: null,
            is_taking_damage: false,
        }
    }

    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.proceed_data_message, 30)
        timerscounter.add(this.constructor.name, timer_id)


        take_control("Sirocco")

    }


    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }
    render() {
        return (<div
            className={'CommonRadarStation'}>
            <PlayersRadarWidget
            />
        </div >)
    }
}
