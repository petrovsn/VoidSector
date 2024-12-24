
import React from 'react'

import { send_command, get_solarflare } from './modules/network/connections.js'
import { AdminRadarWidget } from './modules/widgets/AdminRadar.js';
import { PerformanceViewer } from './modules/widgets/PerformanceWidget.js';
import './styles/Administration.css'
import { ShipsStateWidget } from './modules/widgets/ShipsStateWidget.js';

import { CommandEditorWidget } from './modules/widgets/CommandEditor.js';
import { timerscounter } from './modules/utils/updatetimers.js';
import { QuestPointsController } from './modules/widgets/QuestPointsController.js';

export class Administration extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            selected: null,
            "sf_timer_value": 0
        }
    }

    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(() => {
            this.forceUpdate()
        }, 30)
        timerscounter.add(this.constructor.name, timer_id)
    }

    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }


    restart_simulation = () => {
        send_command("server", null, "restart", null, true)
    }

    autoUpdateMap = (value) => {
        send_command("hBodiesPool", "admin", "set_realtime_update", { 'value': value })
    }

    reload_predictors = () =>{
        send_command("server", "admin", "reload_predictors", {})
    }


    render() {
        return (<div

            className='Administration'>
            <b>Administration</b>
            <div className='AdminControlPanel'>



            </div>
            <div
                style={{
                    "display": "flex",
                    "flex-directin": "row"
                }}>
                <AdminRadarWidget />
                <div className='SystemsSection'>
                    <div className='SystemsSectionLevel'>
                        <PerformanceViewer>

                        </PerformanceViewer>
                    </div>

                    <button onClick={(e)=>{this.reload_predictors()}}>
                        RELOAD PREDICTORS 
                    </button>

                    <QuestPointsController />
                    
                </div>
            </div>

        </div>)
    }
}
