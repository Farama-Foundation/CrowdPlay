import { useMemo } from 'react'
import {
  AreaChart, CartesianGrid, XAxis, Area, ReferenceLine, Label,
} from 'recharts'

export default function useColumnsConfig() {
  return useMemo(() => ([{

    key: 'metric',
    title: 'Metric',
    dataIndex: 'metric',
  }, {
    key: 'this_visit',
    title: 'You',
    dataIndex: 'your_score',
    align: 'center',
  }, {
    key: 'all_visits',
    title: 'Compared to everyone else',
    align: 'center',
    render: scores => (
      <span>
        You scored higher than
        {' '}
        {scores.percentile}
        % of participants.
        {/* {scores.your_rank}
        {' '}
        out of
        {' '}
        {scores.out_of}
        . */}
      </span>
    ),
  }, {
    key: 'all_visits',
    title: 'Histogram',
    align: 'center',
    render: scores => (
      <div className="all_visits-chart">
        {/* <ResponsiveContainer width="100%" height="100%"> */}
        <AreaChart width={300} height={200} data={scores.histogram}>

          {/* <Curve type="monotone" dataKey="y" stroke="#8884d8" dot={false} /> */}
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" type="number" domain={['auto', 'auto']} />
          {/* <YAxis /> */}
          <Area type="monotone" dataKey="y" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
          <ReferenceLine x={scores.your_score_raw} stroke="red" strokeWidth="2" alwaysShow>
            <Label value="You" angle="0" position="bottom" offset="20" />
          </ReferenceLine>
        </AreaChart>
        {/* </ResponsiveContainer> */}
      </div>
    ),
  },

  ]), [])
}
