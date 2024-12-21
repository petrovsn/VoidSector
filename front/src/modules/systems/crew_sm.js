import React from 'react'
import { send_command, get_system_state } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';
import { get_locales } from '../locales/locales.js'

export class CrewControlWidget extends React.Component {
    constructor(props) {
        super(props);


        this.state = {
            data: {
                total_crew: -1,
                teams: {}
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
        let crew_data = get_system_state("crew_sm")
        let med_data = get_system_state("med_sm")
        if (med_data) {
            crew_data["wounded"] = med_data["hospital"]["units"]
            crew_data["hospitale_cap"] = med_data["hospital"]["capacity"]
        }
        this.setState({ "data": crew_data })
    }

    get_teams_list = () => {
        let result = []
        for (let team_name in this.state.data.teams) {
            result.push(<RepairTeamWidget mark_id={this.state.data.mark_id} team_data={this.state.data.teams[team_name]} />)
        }
        return result
    }


    render() {
        if (!this.state.data) return <div className='SystemControlWidget'><b>CrewControl</b></div>
        return (
            <div className='SystemControlWidget'>
                <b>{get_locales("CrewControl")}</b>
                <label>{get_locales("total_crew")}:{this.state.data["total_crew"]}</label>
                <label>{get_locales("free_crew")}:{this.state.data["free_crew"]}</label>
                <label>{get_locales("hospital")}:{this.state.data["wounded"]}/{this.state.data["hospitale_cap"]}</label>
                {this.get_teams_list()}
            </div>
        )
    }

}


export class RepairTeamWidget extends React.Component {




    onRemoveCrewMember = (e) => {
        send_command("ship.crew_sm", this.props.mark_id, "remove_crew_from_team", { "team_name": this.props.team_data["name"] })
    }
    onAddCrewMember = (e) => {
        send_command("ship.crew_sm", this.props.mark_id, "add_crew_to_team", { "team_name": this.props.team_data["name"] })
    }

    render() {
        let header = <span><b>{get_locales(this.props.team_data["name"])}: </b><i>{get_locales(this.props.team_data["state"])}</i></span>
        if (this.props.mode === "engineer") {
            header = <b>{get_locales(this.props.team_data["name"])}</b>
        }
        return (
            <div className='RepairTeamWidget'>
                <img src={"portraits/" + this.props.team_data["name"] + ".jpg"} alt='face'></img>
                <div className='RepairTeamWidget_data'>
                    {header}
                    <progress value={this.props.team_data["loadout"]} max={1}></progress>
                    {this.props.mode !== "engineer" ?
                        <div>
                            <button onClick={this.onRemoveCrewMember}>-</button>
                            <label>{this.props.team_data["crew"]}/10</label>
                            <button onClick={this.onAddCrewMember}>+</button>
                        </div> :
                        <div>

                            <label>{this.props.team_data["crew"]}/10</label>

                        </div>}
                </div>
            </div>
        )
    }

}
