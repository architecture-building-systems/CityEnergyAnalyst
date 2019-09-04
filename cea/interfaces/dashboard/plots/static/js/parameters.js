const { Form, Input, Icon, Switch, Select, Divider } = antd;

const ceaParameter = (param, getFieldDecorator) => {
  const { name, type, value, help } = param;

  const openDialog = () => {
    console.log('open dialog')
  };

  let input = [];

  if (["IntegerParameter", "RealParameter"].includes(type)) {
    const stringValue = value !== null ? value.toString() : "";
    const regex =
      type === "IntegerParameter"
        ? /^(?:[1-9][0-9]*|0)$/
        : /^(?:[1-9][0-9]*|0)(\.\d+)?$/;
    input = (
      <React.Fragment>
        {getFieldDecorator(name, {
          initialValue: stringValue,
          rules: [
            {
              type: "number",
              message: `Please enter an ${
                type === "IntegerParameter" ? "integer" : "float"
              }`,
              transform: num => {
                if (num === "") return 0;
                return regex.test(num) ? Number(num) : NaN;
              }
            }
          ]
        })(<Input />)}
      </React.Fragment>
    );
  } else if (["PathParameter", "FileParameter"].includes(type)) {
    input = (
      <React.Fragment>
        {getFieldDecorator(name, {
          initialValue: value
        })(
          <Input
            addonAfter={
              <button
                className={type}
                type="button"
                style={{ height: "30px", width: "50px" }}
                onClick={openDialog}
              >
                <Icon type="ellipsis" />
              </button>
            }
          />
        )}
      </React.Fragment>
    );
  } else if (
    [
      "ChoiceParameter",
      "PlantNodeParameter",
      "ScenarioNameParameter",
      "SingleBuildingParameter"
    ].includes(type)
  ) {
    const { choices } = param;
    const { Option } = Select;
    const Options = choices.map(choice => (
      <Option key={choice} value={choice}>
        {choice}
      </Option>
    ));
    input = (
      <React.Fragment>
        {getFieldDecorator(name, {
          initialValue: value
        })(<Select>{Options}</Select>)}
      </React.Fragment>
    );
  } else if (["MultiChoiceParameter", "BuildingsParameter"].includes(type)) {
    const { choices } = param;
    const { Option } = Select;
    const Options = choices.map(choice => (
      <Option key={choice} value={choice}>
        {choice}
      </Option>
    ));
    input = (
      <React.Fragment>
        {getFieldDecorator(name, {
          initialValue: value
        })(
          <Select
            mode="multiple"
            style={{ width: "100%" }}
            placeholder="Nothing Selected"
            showArrow
            maxTagCount={10}
          >
            {Options}
          </Select>
        )}
      </React.Fragment>
    );
  } else if (type === "WeatherPathParameter") {
    const { choices } = param;
    const { Option } = Select;
    const Options = Object.keys(choices).map(choice => (
      <Option key={choice} value={choices[choice]}>
        {choice}
      </Option>
    ));
    input = (
      <React.Fragment>
        {getFieldDecorator(name, {
          initialValue: value
        })(
          <Select
            dropdownRender={menu => (
              <div>
                {menu}
                <Divider style={{ margin: "4px 0" }} />
                <div
                  style={{ padding: "8px", cursor: "pointer" }}
                  onMouseDown={openDialog}
                  role="button"
                  tabIndex={0}
                >
                  <Icon type="plus" /> Browse for weather file
                </div>
              </div>
            )}
          >
            {Options}
          </Select>
        )}
      </React.Fragment>
    );
  } else if (type === "BooleanParameter") {
    input = (
      <React.Fragment>
        {getFieldDecorator(name, {
          initialValue: value
        })(<Switch defaultChecked={value} />)}
      </React.Fragment>
    );
  } else {
    input = (
      <React.Fragment>
        {getFieldDecorator(name, {
          initialValue: value
        })(<Input />)}
      </React.Fragment>
    );
  }

  return (
    <Form.Item
      label={name}
      labelCol={{ span: 6 }}
      wrapperCol={{ span: 11, offset: 1 }}
      key={name}
    >
      {input}
      <br />
      <small style={{ display: "block", lineHeight: "normal" }}>{help}</small>
    </Form.Item>
  );
};
