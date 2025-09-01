//go:build tools
// +build tools

package machine

import (
	_ "github.com/Khan/genqlient"
)

//go:generate go run github.com/Khan/genqlient
